import React from "react";
import { render } from "@testing-library/react";
import { IntlProvider } from "react-intl";
import "@testing-library/jest-dom/extend-expect";
import AutotestRunItem from "./AutotestRunItem";
import { IAutotestsRunsList } from "@/interfaces/AutoTests";
import { MemoryRouter } from "react-router-dom";

const mockAutoRuns: IAutotestsRunsList[] = [
  {
    id: "5e2924e5-c9af-464b-946d-bdeabb7a035a",
    absolute_url: "/",
    stateName: "InProgress",
    name: "Auto test 1",
    startedDate: "2025-03-25T16:47:44.628826+03:00",
    completedDate: "2025-03-27T16:47:44.628834+03:00",
    runCount: 132,
    autoTestsCount: 5,
    statistics: {
      count: 14,
      InProgress: 2,
      Passed: 1,
      Failed: 6,
      Skipped: 4,
      Blocked: 2,
    },
    code: "EQA-AR-12",
  },
  {
    id: "5e2924e5-c9af-464b-946d-bdeabb7a035b",
    absolute_url: "/",
    stateName: "Stopped",
    name: "TestRun_2025-03-27T16:47:54",
    startedDate: "2025-03-24T16:47:54.628826+03:00",
    completedDate: "2025-03-27T16:47:54.628834+03:00",
    runCount: 2,
    autoTestsCount: 16,
    statistics: null,
    code: "EQA-AR-13",
  },
  {
    id: "5e2924e5-c9af-464b-946d-bdeabb7a035d",
    absolute_url: "/",
    stateName: "Completed",
    name: "TestRun_2025-03-27T16:48:14",
    startedDate: "2025-03-26T16:48:14.628826+03:00",
    completedDate: "2025-03-27T16:48:14.628834+03:00",
    runCount: 4,
    autoTestsCount: 750,
    statistics: {
      count: 14,
      InProgress: 2,
      Passed: 1,
      Failed: 6,
      Skipped: 4,
      Blocked: 2,
    },
    code: "EQA-AR-14",
  },
  {
    id: "5e2924e5-c9af-464b-946d-bdeabb7a035e",
    absolute_url: "/",
    stateName: "NotStarted",
    name: "TestRun_2025-03-27T16:48:24",
    startedDate: "2025-03-25T16:48:24.628826+03:00",
    completedDate: "2025-03-27T16:48:24.628834+03:00",
    runCount: 5,
    autoTestsCount: 17,
    statistics: {
      count: 14,
      InProgress: 2,
      Passed: 1,
      Failed: 6,
      Skipped: 4,
      Blocked: 2,
    },
    code: "EQA-AR-15",
  },
];

describe("AutotestRunItem", () => {
  it("should render correctly", () => {
    const { getByText, container } = render(
      <MemoryRouter>
        <IntlProvider locale='en'>
          <AutotestRunItem
            name={mockAutoRuns[0].name}
            absoluteUrl={mockAutoRuns[0].absolute_url}
            stateName={mockAutoRuns[0].stateName}
            startedDate={mockAutoRuns[0].startedDate}
            completedDate={mockAutoRuns[0].completedDate}
            runCount={mockAutoRuns[0].runCount}
            casesCount={mockAutoRuns[0].autoTestsCount}
            statistics={mockAutoRuns[0].statistics}
            code={mockAutoRuns[0].code}
          />
        </IntlProvider>
      </MemoryRouter>
    );

    const element = container.querySelector(".item");

    expect(element).toBeInTheDocument();

    const link = container.querySelector("a");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", mockAutoRuns[0].absolute_url);
    expect(getByText(mockAutoRuns[0].name)).toBeInTheDocument();
    expect(getByText(mockAutoRuns[0].code)).toBeInTheDocument();
    expect(getByText(mockAutoRuns[0].runCount.toString())).toBeInTheDocument();
    expect(
      getByText(mockAutoRuns[0].autoTestsCount.toString())
    ).toBeInTheDocument();
  });

  it("should render all statuses", () => {
    mockAutoRuns.forEach((run, index) => {
      const { getByText } = render(
        <MemoryRouter>
          <IntlProvider locale='en'>
            <AutotestRunItem
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
          </IntlProvider>
        </MemoryRouter>
      );
      expect(getByText(run.name)).toBeInTheDocument();
      expect(
        getByText(
          run.stateName.charAt(0).toUpperCase() +
            run.stateName.slice(1).toLowerCase()
        )
      ).toBeInTheDocument();
    });
  });
});
