import { Alert, Box, Button, Container, Snackbar } from '@mui/material'
import dayjs from 'dayjs'
import { useRouter } from 'next/router'
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
  const router = useRouter()
  const [isLoadingPDF, setIsLoadingPDF] = useState(false)
  // After a successful download we nudge the user to ask the AI assistant
  // follow-up questions about their report.
  const [showChatSuggest, setShowChatSuggest] = useState(false)
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

  // Open the AI chat pre-loaded with this report's context (name, birthday,
  // main number) so the assistant knows which report the user is asking about.
  const goToChat = () => {
    setShowChatSuggest(false)
    const facts: string[] = []
    if (userInfo.mainNumber) facts.push(`số chủ đạo ${userInfo.mainNumber}`)
    if (userInfo.birthday) facts.push(`ngày sinh ${userInfo.birthday}`)
    const detail = facts.length ? ` (${facts.join(', ')})` : ''
    const prefill = `Tôi vừa xem báo cáo thần số học của ${userInfo.name}${detail}. Bạn hãy giải thích chi tiết và tư vấn giúp tôi dựa trên các chỉ số này nhé.`
    router.push({ pathname: '/chat', query: { prefill } })
  }

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
      // Report is in hand — invite the user to chat with the AI assistant.
      setShowChatSuggest(true)
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
              <BoxExportPDF
                isPaid={isPaid}
                onClick={handleDownloadPDF}
                onChatClick={goToChat}
              />
            </Box>
          )}
        </Container>
      </Box>
      {/* Free viewers get a sticky deep-link to unlock the full report. */}
      {report && !isPaid && <StickyPurchaseBar />}

      {/* Post-download nudge: hỏi đáp với Trợ lý AI về báo cáo vừa tải. */}
      <Snackbar
        open={showChatSuggest}
        autoHideDuration={12000}
        onClose={() => setShowChatSuggest(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          variant="filled"
          onClose={() => setShowChatSuggest(false)}
          action={
            <Button
              color="inherit"
              size="small"
              variant="outlined"
              onClick={goToChat}
            >
              Chat với AI
            </Button>
          }
        >
          Đã tải báo cáo! Trò chuyện với Trợ lý AI để được giải đáp chi tiết về
          các chỉ số của bạn.
        </Alert>
      </Snackbar>
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
