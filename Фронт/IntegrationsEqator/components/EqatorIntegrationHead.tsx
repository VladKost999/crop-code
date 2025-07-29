import Icon from '@/components/Icon/Icon'
import classNames from 'classnames'
import React from 'react'
import styles from '../../Integrations/styles/card.module.scss'

const EqatorIntegrationHead = (): JSX.Element => {
  const roundColor = classNames(styles.round, styles.transparent)

  return (
    <div className={styles.card__header}>
      <div className={styles.card__left}>
        <div className={roundColor} />
        <Icon className={styles.card__icon} src='eqatorIcon' />
        <div className={styles.card__title}>Eqator utility</div>
      </div>
    </div>
  )
}

export default EqatorIntegrationHead
