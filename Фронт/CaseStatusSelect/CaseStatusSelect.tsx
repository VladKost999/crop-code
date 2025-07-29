import Icon from '@/components/Icon/Icon'
import MenuItem from '@/components/MenuItem/MenuItem'
import { TCaseStatus, TCaseType } from '@/interfaces/Types'
import classNames from 'classnames'
import React, { forwardRef, useEffect, useState } from 'react'
import { FormattedMessage, useIntl } from 'react-intl'
import Select from '../Select'
import { CASE_TYPES } from '@/const'
import style from './styles/casestatusselect.module.scss'

interface IProps {
  caseType: TCaseType
  stepsCount: number
  className?: string
  handleChange?: (e: any) => void
  value?: TCaseStatus
  required?: boolean
  clearable?: boolean
  labelLeft?: boolean
  canUserApproveCases?: boolean
}

const icons = {
  approved: 'checked',
  refinement: 'refinement',
  draft: 'draft'
} as const

const CaseStatusSelect = (
  {
    caseType,
    stepsCount,
    labelLeft = false,
    className = '',
    handleChange,
    value = 'draft',
    required = false,
    clearable = true,
    canUserApproveCases = false
  }: IProps,
  ref
): React.ReactElement => {
  const intl = useIntl()
  const isTask = caseType === CASE_TYPES.task

  const disableConditions = {
    approved: () => !(canUserApproveCases && (stepsCount !== 0 || isTask)),
    refinement: () => stepsCount === 0 && !isTask,
    draft: () => false
  }

  const [statusMessage, setStatusMessage] = useState('')

  useEffect(() => {
    if (stepsCount === 0 && !isTask && value !== 'draft' && (handleChange != null)) {
      setStatusMessage(intl.formatMessage({
        id: 'case.no_steps',
        defaultMessage: "You cannot change the case status to 'Approved' or 'Refinement' without adding steps"
      }))
      handleChange({ target: { value: 'draft' } })
    } else { setStatusMessage('') }
  }, [stepsCount])

  return (
    <Select
      labelLeft={labelLeft}
      ref={ref}
      className={classNames({
        [style.form]: true,
        [className]: Boolean(className)
      })}
      placeholder={intl.formatMessage({
        id: 'case.form.status',
        defaultMessage: 'Status'
      })}
      required={required}
      label={intl.formatMessage({
        id: 'case.form.status',
        defaultMessage: 'Status'
      })}
      onChange={handleChange}
      clearable={clearable}
      value={value}
      error={statusMessage}
    >
      {icons[value] !== undefined
        ? (
          <Icon
            src={icons[value]}
            className={style[`${icons[value]}`]}
            slot='prefix'
          />
          )
        : null}
      {Object.entries(icons).map(([iconValue, iconSrc]) => (
        <MenuItem
          key={iconValue}
          value={iconValue}
          className={style.project_item}
          disabled={disableConditions[iconValue]()}
        >
          <Icon src={iconSrc} className={style[`${iconSrc}`]} />
          <FormattedMessage
            id={`status.case.${iconValue.toLowerCase()}`}
            defaultMessage={iconValue}
          />
        </MenuItem>
      ))}
    </Select>
  )
}

export default forwardRef(CaseStatusSelect)
