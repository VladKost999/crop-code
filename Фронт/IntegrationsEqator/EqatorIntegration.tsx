import React, { useState } from 'react'
import { ControlledAccordion } from '@/components/Accordion'
import EqatorIntegrationHead from './components/EqatorIntegrationHead'
import EqatorForm from './components/EqatorForm'
import styles from '../Integrations/styles/card.module.scss'

const EqatorIntegration = (): JSX.Element => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <ControlledAccordion
      className={styles.card}
      setIsOpen={setIsOpen}
      isOpen={isOpen}
      head={<EqatorIntegrationHead />}
    >
      <EqatorForm />
    </ControlledAccordion>
  )
}

export default EqatorIntegration
