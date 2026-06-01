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
  BannerSearchResultPage,
  ChallengesSection,
  CoreNumbersSection,
  LifePeaksSection,
  MainNumberDetail,
  PersonalCycleSection,
  PowerChartSection,
} from '@/modules/result'
import { BoxExportPDF } from '@/modules/result/parts'
import { useStore } from '@/store/useStore'

import type { MainstreamNumberParams } from '../api/numerologyApi'
import numerologyApi from '../api/numerologyApi'

const IS_VIP = false

const SearchResultPage: NextPageWithLayout = () => {
  const [isLoadingPDF, setIsLoadingPDF] = useState(false)
  const { customerInfo } = useStore((state) => ({
    customerInfo: state.customerInfo,
  }))

  const params: MainstreamNumberParams = useMemo(
    () => ({
      full_name: customerInfo.name,
      birth_day: dayjs(customerInfo.birthDay)?.format('DDMMYYYY') || '',
      phone: customerInfo.phoneNumber,
    }),
    [customerInfo]
  )

  const { data: reportRes, isLoading } = useSWR(
    customerInfo.birthDay ? ['numerology_report', params] : null,
    () => numerologyApi.getNumerologyReport(params)
  )
  const report = reportRes?.data

  const userInfo = useMemo(
    () => ({
      name: customerInfo.name,
      birthday: dayjs(customerInfo.birthDay)?.format('DD/MM/YYYY') || '',
      mainNumber: Number(report?.so_chu_dao.code) || 0,
      isVip: IS_VIP,
    }),
    [customerInfo, report]
  )

  const handleDownloadPDF = async () => {
    setIsLoadingPDF(true)
    try {
      const response = await numerologyApi.getMainstreamPDF(params)
      const blob = new Blob([response], { type: 'application/pdf' })
      const fileURL = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = fileURL
      link.setAttribute('download', `${customerInfo.name.split(' ').join('_')}.pdf`)
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
      <Loading isOpen={isLoading || isLoadingPDF} />
      <BannerSearchResultPage userInfo={userInfo} />
      <Box pt={9} pb={23}>
        <Container maxWidth={false}>
          {report && (
            <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 6 }}>
              <MainNumberDetail indicator={report.so_chu_dao} />
              <CoreNumbersSection core={report.core_numbers} isVip={IS_VIP} />
              <LifePeaksSection peaks={report.peaks} isVip={IS_VIP} />
              <ChallengesSection challenges={report.challenges} isVip={IS_VIP} />
              <PersonalCycleSection personal={report.personal} isVip={IS_VIP} />
              <PowerChartSection
                powerChart={report.power_chart}
                missingNumbers={report.missing_numbers}
                isVip={IS_VIP}
              />
              <BoxExportPDF onClick={handleDownloadPDF} />
            </Box>
          )}
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

export default SearchResultPage
