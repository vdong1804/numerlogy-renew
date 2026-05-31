import { Box, Container } from '@mui/material'
import dayjs from 'dayjs'
import type { ReactElement } from 'react'
import { useMemo, useState } from 'react'
import useSWR from 'swr'

import NotFound404 from '@/components/common/NotFound404'
import { Loading } from '@/components/loading'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import {
  ApproachAttitude,
  AttitudeIndicator,
  BannerSearchResultPage,
  CapacityIndicator,
  ChallengeIndicators,
  ChallengePersonalityIndicators,
  ChallengeSoulIndicators,
  CharacterGroup,
  ChiSoNoNghiep,
  CycleFortunes,
  LifeCycle,
  LifeNumber,
  MatureCapacityIndicators,
  MatureIndicators,
  MissionIndicators,
  MonthIndicators,
  MotivationIndicator,
  NaturalPowerIndicator,
  OvercomeDifficulties,
  PersonalityIndicators,
  PowerChart,
  PyramidNumerology,
  SoulIndicators,
  SummaryChart,
  ThinkingIndicator,
  WeaknessIndicators,
  YearIndicators,
} from '@/modules/result'
import { BoxExportPDF } from '@/modules/result/parts'
import { useStore } from '@/store/useStore'

import type { MainstreamNumberParams } from '../api/numerologyApi'
import numerologyApi from '../api/numerologyApi'

const SearchResultPage: NextPageWithLayout = () => {
  const [isloadingPDF, setIsLoadingPDF] = useState(false)
  const { customerInfo } = useStore((state) => ({
    customerInfo: state.customerInfo,
  }))

  const mainstreamNumberParamss: MainstreamNumberParams = useMemo(
    () => ({
      full_name: customerInfo.name,
      birth_day: dayjs(customerInfo.birthDay)?.format('DDMMYYYY') || '',
      phone: customerInfo.phoneNumber,
    }),
    [customerInfo]
  )
  const { data: mainstreamNumberInfo, isLoading } = useSWR(
    customerInfo.birthDay ? 'mainstream_number' : null,
    () => numerologyApi.getMainstreamNumber(mainstreamNumberParamss)
  )
  const userInfo = useMemo(() => {
    return {
      name: customerInfo.name,
      birthday: dayjs(customerInfo.birthDay)?.format('DD/MM/YYYY') || '',
      mainNumber: mainstreamNumberInfo?.data.so_chu_dao.code || 0,
      isVip: false,
    }
  }, [customerInfo, mainstreamNumberInfo])
  const handleDownloadPDF = async () => {
    setIsLoadingPDF(true)
    try {
      const response = await numerologyApi.getMainstreamPDF(
        mainstreamNumberParamss
      )
      const blob = new Blob([response], { type: 'application/pdf' })
      const fileURL = URL.createObjectURL(blob)
      // window.open(fileURL)
      const link = document.createElement('a')
      link.href = fileURL
      link.setAttribute(
        'download',
        `${customerInfo.name.split(' ').join('_')}.pdf`
      )
      document.body.appendChild(link)
      link.click()
    } catch (error) {
      // eslint-disable-next-line no-console
      console.log(error)
    } finally {
      setIsLoadingPDF(false)
    }
  }
  if (!customerInfo.name) return <NotFound404 />

  return (
    <Box className="search-results-page-wrapper">
      <Loading isOpen={isLoading || isloadingPDF} />
      <BannerSearchResultPage userInfo={userInfo} />
      <Box pt={9} pb={23}>
        <Container maxWidth={false}>
          <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 3.75 }}>
            <CycleFortunes isVip={false} />
            <CharacterGroup isVip={false} />
            <LifeNumber isVip={false} />
            <LifeCycle isVip={false} />
            <PyramidNumerology isVip={false} />
            <YearIndicators isVip={false} />
            <MonthIndicators isVip={false} />
            <MissionIndicators isVip={false} />
            <ChallengeIndicators isVip={false} />
            <MatureIndicators isVip={false} />
            <MatureCapacityIndicators isVip={false} />
            <SoulIndicators isVip={false} />
            <ChallengeSoulIndicators isVip={false} />
            <PersonalityIndicators isVip={false} />
            <ChallengePersonalityIndicators isVip={false} />
            <WeaknessIndicators isVip={false} />
            <ChiSoNoNghiep isVip={false} />
            <PowerChart isVip={false} />
            <SummaryChart isVip={false} />
            <AttitudeIndicator isVip={false} />
            <NaturalPowerIndicator isVip={false} />
            <OvercomeDifficulties isVip={false} />
            <ThinkingIndicator isVip={false} />
            <MotivationIndicator isVip={false} />
            <CapacityIndicator isVip={false} />
            <ApproachAttitude isVip={false} />
            <BoxExportPDF onClick={handleDownloadPDF} />
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
SearchResultPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta title="Xem kết quả tra cứu" description="Xem kết quả tra cứu" />
      }
    >
      {page}
    </Main>
  )
}
// export default dynamic(() => Promise.resolve(SearchResultPage), {
//   ssr: false,
// })
export default SearchResultPage
