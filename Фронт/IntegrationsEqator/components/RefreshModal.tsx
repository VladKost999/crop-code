import React from 'react'
import { FormattedMessage, useIntl } from 'react-intl'
import style from '../styles/eqator.module.scss'
import { ModalAction } from '@/components/Modal'

interface IProps {
  onClose: () => void
  onSumbit: () => void
}

const RefreshModal = ({
  onClose,
  onSumbit
}: IProps): React.ReactElement => {
  const intl = useIntl()
  return (
    <ModalAction onCancel={onClose} onAction={onSumbit} actionButtonIcon='refresh' confirmText={intl.formatMessage({ id: 'common.refresh', defaultMessage: 'Refresh' })}>
      <div className={style.warning__text}>
        <FormattedMessage
          id='integfations.eqator.warning_text'
          defaultMessage='Please note that after the token is updated, you will need to update the integration URL in your code.'
        />
      </div>
    </ModalAction>
  )
}

export default RefreshModal
