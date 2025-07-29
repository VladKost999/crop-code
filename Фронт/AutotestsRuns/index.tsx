import React from 'react'
import Container from '@/components/Container'
import SearchInput from '@/components/Input/SearchInput/SearchInput'
import ListContent from '@/components/ListContent'
import Pagination from '@/components/Pagination'
import AutotestRunStatusSelect from '@/components/Select/AutotestRunStatusSelect'
import Title from '@/components/Title'
import Wrapper from '@/components/Wrapper'
import AutotestRunItem from './components/AutotestRunItem'
import { FormattedMessage, useIntl } from 'react-intl'
import { TAutotestRunStatus } from '@/interfaces/Types'
import useSWR from 'swr'
import { useDebounce, useProjectObject, useStores } from '@/hooks'
import style from './styles/autoruns.module.scss'

const PAGE_SIZE = 20

const AutotestsRuns = (): React.ReactElement => {
  const [search, setSearch] = React.useState('')
  const [status, setStatus] = React.useState<TAutotestRunStatus | ''>('')
  const [page, setPage] = React.useState(1)

  const intl = useIntl()
  const { api } = useStores()
  const { id: projectId } = useProjectObject()
  const debounceSearch = useDebounce(search)
  const isFiltered = debounceSearch !== '' || status !== ''

  const {
    data: autotestsRuns,
    isLoading,
    error
  } = useSWR(
    {
      projectId,
      page,
      page_size: PAGE_SIZE,
      q: debounceSearch !== '' ? debounceSearch : undefined,
      stateName: status !== '' ? status : undefined
    },
    api.getAutotestsRuns
  )

  const handleSearch = (value): void => {
    setSearch(value)
  }

  const handleChangeStatus = (e): void => {
    setStatus(e.target.value)
  }

  return (
    <Container>
      <Wrapper>
        <Title type='h1'>
          <FormattedMessage
            id='titles.autotests.runs'
            defaultMessage='Autotests Runs'
          />
        </Title>

        <div className={style.filters}>
          <AutotestRunStatusSelect
            className={style.filters__select}
            handleChange={handleChangeStatus}
            value={status}
          />
          <SearchInput
            className={style.filters__search}
            handleChange={handleSearch}
            value={search}
          />
        </div>

        <ListContent
          isLoading={isLoading}
          error={error}
          hasData={
            autotestsRuns?.count !== undefined && autotestsRuns?.count > 0
          }
          emptyListIcon={isFiltered ? 'search' : 'autorun'}
          emptyListText={
            isFiltered
              ? intl.formatMessage({
                id: 'empty_results.search',
                defaultMessage: 'Nothing found for your request'
              })
              : intl.formatMessage({
                id: 'autotests.runs.no_runs',
                defaultMessage: 'No Autotests Runs created'
              })
          }
        >
          <div className={style.list}>
            {autotestsRuns?.results.map((run) => (
              <AutotestRunItem
                key={run.id}
                name={run.name}
                absoluteUrl={run.absolute_url}
                stateName={run.stateName}
                startedDate={run.startedDate}
                completedDate={run.completedDate}
                runCount={run.runCount}
                casesCount={run.autoTestsCount}
                statistics={run.statistics}
                code={run.code}
              />
            ))}
          </div>

          <div className={style.pagination}>
            <Pagination
              currentPage={page}
              total={autotestsRuns?.count ?? 0}
              pageSize={PAGE_SIZE}
              handleChange={setPage}
            />
          </div>
        </ListContent>
      </Wrapper>
    </Container>
  )
}

export default AutotestsRuns
