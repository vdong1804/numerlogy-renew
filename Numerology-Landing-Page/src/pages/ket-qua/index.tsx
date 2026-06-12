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
  KarmicDebtSection,
  LifePeaksSection,
  MainNumberDetail,
  PersonalCycleSection,
  PowerChartSection,
} from '@/modules/result'
import { downloadReportBlob } from '@/lib/my-account-api'
import { BoxExportPDF } from '@/modules/result/parts'
import StickyPurchaseBar from '@/modules/result/parts/StickyPurchaseBar'
import { useStore } from '@/store/useStore'

import type { MainstreamNumberParams } from '../api/numerologyApi'
import numerologyApi from '../api/numerologyApi'

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
  // Entitlement is server-driven: "paid" only when the logged-in user owns a
  // matching paid order. Anonymous/free viewers see locked sections as teasers.
  const isPaid = reportRes?.tier === 'paid'

  const userInfo = useMemo(
    () => ({
      name: customerInfo.name,
      birthday: dayjs(customerInfo.birthDay)?.format('DD/MM/YYYY') || '',
      mainNumber: Number(report?.so_chu_dao?.code) || 0,
      isVip: isPaid,
    }),
    [customerInfo, report, isPaid]
  )

  const handleDownloadPDF = async () => {
    setIsLoadingPDF(true)
    try {
      // Pick the download path the backend resolved:
      //  - 'order'  → the fulfilled UserReport PDF (per-report purchase)
      //  - 'quota'  → premium subscriber, full PDF via the quota endpoint
      //  - 'free'   → public reduced PDF
      let blob: Blob
      const pdfSource = reportRes?.pdf_source
      if (pdfSource === 'order' && reportRes?.report_download_id) {
        blob = await downloadReportBlob(reportRes.report_download_id)
      } else if (pdfSource === 'quota') {
        const buffer = await numerologyApi.getMainstreamPDF(params)
        blob = new Blob([buffer], { type: 'application/pdf' })
      } else {
        const buffer = await numerologyApi.getFreePDF(params)
        blob = new Blob([buffer], { type: 'application/pdf' })
      }
      const fileURL = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = fileURL
      link.setAttribute('download', `${customerInfo.name.split(' ').join('_')}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(fileURL)
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
          {report?.so_chu_dao && (
            <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 6 }}>
              <MainNumberDetail indicator={report.so_chu_dao} />
              <CoreNumbersSection core={report.core_numbers} />
              <LifePeaksSection peaks={report.peaks} />
              <ChallengesSection challenges={report.challenges} />
              <KarmicDebtSection karmicDebt={report.karmic_debt} />
              <PersonalCycleSection personal={report.personal} />
              <PowerChartSection
                powerChart={report.power_chart}
                missingNumbers={report.missing_numbers}
              />
              <BoxExportPDF isPaid={isPaid} onClick={handleDownloadPDF} />
            </Box>
          )}
        </Container>
      </Box>
      {/* Free viewers get a sticky deep-link to unlock the full report. */}
      {report && !isPaid && <StickyPurchaseBar />}
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
