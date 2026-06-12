import { Box, Grid } from '@mui/material'

import type { Challenge } from '@/models'

import NumberCard from './NumberCard'
import SectionHeading from './parts/SectionHeading'

export interface ChallengesSectionProps {
  challenges: Challenge[]
}

/** The 4 life challenges rendered as cards, labelled by stage. */
export default function ChallengesSection({
  challenges,
}: ChallengesSectionProps) {
  if (!challenges?.length) return null
  return (
    <Box component="section">
      <SectionHeading
        title="Thử Thách Cuộc Đời"
        subtitle="Những bài học vũ trụ gửi đến bạn qua từng giai đoạn"
      />
      <Grid container spacing={2.5} mt={0}>
        {challenges.map((challenge) => (
          <Grid key={challenge.stage} item xs={12} sm={6} lg={3}>
            <NumberCard
              label={`Thử thách ${challenge.stage}`}
              indicator={challenge}
              compact
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
