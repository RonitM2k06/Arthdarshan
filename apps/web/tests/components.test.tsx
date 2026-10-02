import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { translate } from "@/lib/i18n";

vi.mock("@/lib/state", () => ({ useApp: () => ({ t: (k: any) => translate("en", k), lang: "en", simple: false }) }));

import { BarChart, LineChart } from "@/components/Charts";
import { DimRows, FingerprintCard, Radar, type Dim, type FP } from "@/components/Fingerprint";

const mk = (id: string, score: number | null, prev: number | null = null): Dim => ({ id, name: `Dim ${id}`, short: id.slice(0, 5), score, previous: prev, change: score != null && prev != null ? score - prev : null,
  n_observations: score == null ? 0 : 3, evidence: score == null ? [] : [{ note: `note ${id}`, value: Math.round(score) }], measured: score != null });
const DIMS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"].map((x, i) => mk(x, i < 7 ? 40 + i * 5 : null, i < 7 ? 30 : null));
const FP: FP = { dimensions: DIMS, strengths: ["g"], opportunities: ["a"], summary: "Your strongest area right now is X.", measured_count: 7 };

describe("Radar", () => {
  it("draws all ten axes and labels with scores; unmeasured dimensions show no invented number", () => {
    const { container } = render(<Radar dims={DIMS} />);
    expect(container.querySelectorAll("g[role='img']").length).toBe(10);
    const labels = Array.from(container.querySelectorAll("text")).map((t) => t.textContent);
    expect(labels.filter((l) => /\d/.test(l ?? "")).length).toBe(7);          // 7 measured -> 7 numeric labels
    expect(labels).toContain("a 40");
    expect(labels.some((l) => l === "h")).toBe(true);                         // unmeasured: name only
  });
  it("exposes an accessible description of every dimension", () => {
    render(<Radar dims={DIMS} />);
    expect(screen.getByRole("group", { name: /Dim a: 40.*Dim h: Not measured yet/ })).toBeInTheDocument();
  });
  it("shows the previous series only when previous data exists", () => {
    const { container, rerender } = render(<Radar dims={DIMS} />);
    expect(container.querySelectorAll("polygon[stroke-dasharray]").length).toBe(1);
    rerender(<Radar dims={DIMS.map((d) => ({ ...d, previous: null }))} />);
    expect(container.querySelectorAll("polygon[stroke-dasharray]").length).toBe(0);
  });
});

describe("DimRows", () => {
  it("shows score, change arrows and expandable evidence; never a score for unmeasured", () => {
    render(<DimRows dims={DIMS} />);
    expect(screen.getAllByText("Not measured yet").length).toBe(3);
    expect(screen.getAllByText(/▲/).length).toBe(7);
    fireEvent.click(screen.getByText("Dim a"));
    expect(screen.getByText("Evidence behind this score")).toBeInTheDocument();
    expect(screen.getByText(/note a/)).toBeInTheDocument();
  });
});

describe("FingerprintCard", () => {
  it("renders the summary and toggles an accessible table view", () => {
    render(<FingerprintCard fp={FP} />);
    expect(screen.getByTestId("fp-summary")).toHaveTextContent("Your strongest area");
    fireEvent.click(screen.getByRole("button", { name: "Show as table" }));
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row").length).toBe(11);
    expect(within(table).getAllByText("—").length).toBeGreaterThan(0);
  });
});

describe("Charts", () => {
  it("LineChart gives a text alternative, a legend and a table view", () => {
    render(<LineChart series={[{ name: "Without charges", points: [100, 108, 117] }, { name: "After charges", points: [100, 105, 110] }]} xLabel="Year" yLabel="Amount" />);
    expect(screen.getByRole("img", { name: /Without charges ends at ₹117.*After charges ends at ₹110/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show as table" }));
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getAllByText("After charges").length).toBeGreaterThan(0);
  });
  it("LineChart never draws more than four series (no cycled hues)", () => {
    const s = Array.from({ length: 6 }, (_, i) => ({ name: `S${i}`, points: [1, 2, 3] }));
    const { container } = render(<LineChart series={s} xLabel="x" yLabel="y" />);
    expect(container.querySelectorAll("polyline").length).toBe(4);
  });
  it("BarChart labels bars and survives zero values", () => {
    const { container } = render(<BarChart bars={[{ label: "A", value: 0 }, { label: "B", value: 500 }]} yLabel="Loss" />);
    expect(container.querySelectorAll("g[role='img']").length).toBe(2);
    expect(screen.getByRole("group", { name: /A ₹0; B ₹500/ })).toBeInTheDocument();
  });
});
