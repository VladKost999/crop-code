import React, { useState, useEffect } from 'react'
import { FormattedMessage, useIntl } from 'react-intl'
import Button from '@/components/Button/Button'
import Icon from '@/components/Icon/Icon'
import { useObjectPage, useResponsiveMedia, useStores } from '@/hooks'
import Tooltip from '@/components/Tooltip'
import Link from '@/components/Link'
import BaseModal from '@/components/Modal/Base'
import RefreshModal from './RefreshModal'
import style from '../styles/eqator.module.scss'

const EqatorForm = (): JSX.Element => {
  const { isMobile } = useResponsiveMedia()
  const { api } = useStores()
  const { id } = useObjectPage()
  const intl = useIntl()

  const [isLoading, setIsLoading] = useState(false)
  const [isVisible, setIsVisible] = useState(false)
  const [isVisibleModal, setIsVisibleModal] = useState(false)
  const [tokenLink, setTokenLink] = useState('')

  const handleRefreshToken = async (): Promise<void> => {
    setIsLoading(true)
    const tokenLink = await api.refreshEqatorIntegrationUrl({ id })
    setTokenLink(tokenLink.url)
    setIsLoading(false)
  }

  const handleCopyLink = (): void => {
    navigator.clipboard
      .writeText(tokenLink)
      .then(() => {
        setIsVisible(true)
        setTimeout(() => {
          setIsVisible(false)
        }, 2000)
      })
      .catch(() => { })
  }

  useEffect(() => {
    const fetchLink = async (): Promise<void> => {
      const response = await api.getEqatorIntegrationUrl(id)
      setTokenLink(response.url)
    }
    void fetchLink()
  }, [])

  return (
    <>
      <hr className={style.line__horizontal} />
      <div className={style.form}>
        <div className={style.form__text}>
          <FormattedMessage
            id='integrations.eqator.text_first'
            defaultMessage='Eqator is a code quality checking utility for Django projects. It leverages tools such as Django unittest, flake8, radon, bandit, and coverage. Eqator helps automate the code quality analysis process and ensures adherence to high standards.'
          />
        </div>
        <div className={style.form__text}>
          <div>
            <FormattedMessage
              id='integrations.eqator.text_second'
              defaultMessage='Further information on functionality and configuration can be found in the <link>documentation</link>.'
              values={{
                link: (chunks) => (
                  <Link target='_blank' to='https://docs.eqator.ru/integrations/Eqator/' className={style.form__link}>
                    {chunks}
                  </Link>
                )
              }}
            />
          </div>
        </div>
        <div className={style.form__block}>
          <div className={style.form__text}>
            <div>
              <FormattedMessage
                id='integrations.eqator.request_warning'
                defaultMessage='Please use this link to send any requests'
              />
              <div className={style.link}>
                {tokenLink}
              </div>
            </div>
          </div>
          <div className={style.btns}>
            <Tooltip
              content={intl.formatMessage({
                id: 'common.link_copied',
                defaultMessage: 'Link copied'
              })}
              trigger='manual'
              open={isVisible}
              placement='bottom'
            >
              <Button
                size={isMobile ? 'sm' : 'med'}
                theme='light'
                onClick={handleCopyLink}
              >
                <Icon src='copy' slot='icon-left' />
                <FormattedMessage id='common.copy' defaultMessage='Copy' />
              </Button>
            </Tooltip>
            <Button
              disabled={isLoading}
              size={isMobile ? 'sm' : 'med'}
              onClick={() => { setIsVisibleModal(true) }}
            >
              <Icon src='refresh' slot='icon-left' />
              <FormattedMessage id='common.refresh' defaultMessage='Refresh' />
            </Button>
          </div>
        </div>
      </div>
      <BaseModal
        open={isVisibleModal}
        onGx-after-hide={() => { setIsVisibleModal(false) }}
        onGx-overlay-dismiss={() => { setIsVisibleModal(false) }}
        hideDefaultClose
        size='medium'
      >
        <RefreshModal
          onClose={() => { setIsVisibleModal(false) }}
          onSumbit={() => { void handleRefreshToken(); setIsVisibleModal(false) }}
        />
      </BaseModal>
    </>
  )
}

export default EqatorForm
