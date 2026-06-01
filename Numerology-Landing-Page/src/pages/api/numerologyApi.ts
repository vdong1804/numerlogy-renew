import type {
  MainstreamNumber,
  News,
  NewsListResponse,
  NumerologyReport,
  ResultResponse,
} from '@/models'

import axiosClient from './axiosClient'

export interface MainstreamNumberParams {
  full_name: string
  birth_day: string
  phone: string
}

interface IResponseMainstreamNumber {
  so_chu_dao: MainstreamNumber
}

const numerologyApi = {
  async getMainstreamNumber(params: MainstreamNumberParams) {
    const url = '/api/so-chu-dao'
    const response = await axiosClient.get<
      ResultResponse<IResponseMainstreamNumber>
    >(url, {
      params,
    })
    return response.data
  },
  // Full data-driven report (single-page summary). Backend: GET /api/numerology-report.
  async getNumerologyReport(params: MainstreamNumberParams) {
    const url = '/api/numerology-report'
    const response = await axiosClient.get<ResultResponse<NumerologyReport>>(
      url,
      { params }
    )
    return response.data
  },
  async getMainstreamPDF(params: MainstreamNumberParams) {
    const url = '/api/so-hoc'
    const config = {
      headers: {
        'Content-Type': 'application/pdf',
      },
    }
    const response = await axiosClient.get(url, {
      params,
      responseType: 'arraybuffer',
      ...config,
    })
    return response.data
  },
  async getNewsTop() {
    const url = '/api/news-top'
    const response = await axiosClient.get<ResultResponse<News[]>>(url)
    return response.data
  },
  // Paginated blog list (newest first). Backend: GET /api/news.
  async getNewsList(params: { limit?: number; offset?: number } = {}) {
    const url = '/api/news'
    const response = await axiosClient.get<NewsListResponse>(url, {
      params: { limit: params.limit ?? 12, offset: params.offset ?? 0 },
    })
    return response.data
  },
  // Single article detail. Backend: GET /api/news/{id} → { data }.
  async getDetailNews(id: string) {
    const url = `/api/news/${id}`
    const response = await axiosClient.get<ResultResponse<News>>(url)
    return response.data.data
  },
}

export default numerologyApi
