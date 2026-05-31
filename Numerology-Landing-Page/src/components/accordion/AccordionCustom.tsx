import type { AccordionProps } from '@mui/material'
import {
  AccordionDetails,
  AccordionSummary,
  styled,
  Typography,
} from '@mui/material'
import MuiAccordion from '@mui/material/Accordion'
import * as React from 'react'

import { IconArrowRightAccordion } from '../icon'

interface AccordionCustomProps {
  title: string
  description: string
}

const Accordion = styled((props: AccordionProps) => (
  <MuiAccordion disableGutters elevation={0} square {...props} />
))(({ theme }) => ({
  border: `1px solid ${theme.palette.background.default}`,
  backgroundColor: theme.palette.background.default,
  color: '#fff',
  borderRadius: '5px',
  '&:hover': {
    border: `1px solid ${theme.palette.primary.main}`,
  },
  transition: 'all ease 0.25s',
}))

export default function AccordionCustom({
  title,
  description,
}: AccordionCustomProps) {
  return (
    <Accordion>
      <AccordionSummary
        expandIcon={<IconArrowRightAccordion />}
        aria-controls="panel-content"
      >
        <Typography variant="h4">{title}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Typography>{description}</Typography>
      </AccordionDetails>
    </Accordion>
  )
}
