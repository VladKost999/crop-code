import React from 'react'

import Link from '@/components/Link'
import Icon, { TIcon } from '@/components/Icon/Icon'
import GroupStatuses from '@/components/GroupStatuses/GroupStatuses'
import { TAutotestRunStatus } from '@/interfaces/Types'
import { useLocale } from '@/hooks'
import AutotestRunStatus from '@/components/Status/AutotestRunStatus'
import { IAutoTestStatistic } from '@/interfaces/AutoTests'
import { IStatistics } from '@/interfaces/Runs'
import style from '../styles/autorunitem.module.scss'
import { useIntl } from 'react-intl'
import Tooltip from '@/components/Tooltip'

interface IProps {
  name: string
  absoluteUrl: string
  stateName: TAutotestRunStatus
  // DateTime in UTC
  startedDate: string
  // DateTime in UTC
  completedDate: string
  runCount: number
  casesCount: number
  statistics: IAutoTestStatistic | null
  code: string
}

const DateBlock = ({
  date,
  icon,
  tooltipText
}: {
  date: string
  icon: TIcon
  tooltipText: string
}): React.ReactElement => {
  const { locale } = useLocale()
  return (
    <Tooltip content={tooltipText}>
      <div className={style.date}>
        <Icon size='xs' src={icon} />
        <span className={style.date__text}>
          {new Intl.DateTimeFormat(locale, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          }).format(new Date(date))}
        </span>
      </div>
    </Tooltip>
  )
}

const CounterBlock = ({
  count,
  icon,
  tooltipText
}: {
  count: number
  icon: TIcon
  tooltipText: string
}): React.ReactElement => {
  return (
    <Tooltip content={tooltipText}>
      <div className={style.date}>
        <Icon size='xs' src={icon} />
        <span className={style.date__text}>{count}</span>
      </div>
    </Tooltip>
  )
}

const AutotestRunItem = ({
  name,
  absoluteUrl,
  stateName,
  startedDate,
  completedDate,
  runCount,
  casesCount,
  statistics,
  code
}: IProps): React.ReactElement => {
  const intl = useIntl()

  const serializedStatistic: IStatistics | null =
    statistics !== null
      ? {
          count: statistics.count,
          passed: statistics.Passed,
          blocked: statistics.Blocked,
          retest: statistics.Skipped,
          failed: statistics.Failed,
          untested: statistics.InProgress,
          status: 'PASSED'
        }
      : null

  return (
    <div className={style.item}>
      <div className={style.item__linkblock}>
        <span className={style.item__code}>{code}</span>

        <Link to={absoluteUrl} className={style.item__link}>
          <Icon src='autorun' />
          <span>{name}</span>
        </Link>
      </div>

      <DateBlock
        date={startedDate}
        icon='clock'
        tooltipText={intl.formatMessage({
          id: 'common.date.start',
          defaultMessage: 'Start date'
        })}
      />

      <DateBlock
        date={completedDate}
        icon='history'
        tooltipText={intl.formatMessage({
          id: 'common.date.complete',
          defaultMessage: 'Completion date'
        })}
      />

      <CounterBlock
        count={casesCount}
        icon='autocase'
        tooltipText={intl.formatMessage({
          id: 'autotests.count.cases',
          defaultMessage: 'Number of cases'
        })}
      />

      <CounterBlock
        count={runCount}
        icon='autoruncount'
        tooltipText={intl.formatMessage({
          id: 'autotests.count.runs',
          defaultMessage: 'Number of runs'
        })}
      />

      {serializedStatistic !== null
        ? (
          <GroupStatuses statistic={serializedStatistic} />
          )
        : null}

      <AutotestRunStatus status={stateName} />
    </div>
  )
}

export default AutotestRunItem
