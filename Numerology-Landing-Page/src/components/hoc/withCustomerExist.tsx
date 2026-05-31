import Router from 'next/router'
import type { ComponentType } from 'react'

import { useStore } from '@/store/useStore'

export function withCustomerExist(Component: ComponentType) {
  // eslint-disable-next-line react/display-name
  return () => {
    const { customerInfo } = useStore((state) => ({
      customerInfo: state.customerInfo,
    }))
    if (!customerInfo.name) Router.push('/')
    return <Component />
  }
}
