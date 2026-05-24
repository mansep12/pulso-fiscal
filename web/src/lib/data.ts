import { institutions } from "@/data/instituciones.sample";
import { spendingRecords } from "@/data/gastos.sample";
import type { ConfidenceLevel, InstitutionSummary, SpendingRecord } from "@/lib/types";

const confidenceRank: Record<ConfidenceLevel, number> = {
  alto: 3,
  medio: 2,
  bajo: 1,
};

export function getInstitutions() {
  return institutions;
}

export function getInstitutionBySlug(slug: string) {
  return institutions.find((institution) => institution.slug === slug) ?? null;
}

export function getSpendingByInstitution(slug: string) {
  return spendingRecords.filter((record) => record.institutionSlug === slug);
}

export function getNationalTotal() {
  return spendingRecords.reduce((total, record) => total + record.amountClp, 0);
}

export function getInstitutionSummaries(): InstitutionSummary[] {
  return institutions
    .map((institution) => {
      const records = getSpendingByInstitution(institution.slug);
      const confidence = records.reduce<ConfidenceLevel>((lowest, record) => {
        return confidenceRank[record.confidence] < confidenceRank[lowest] ? record.confidence : lowest;
      }, "alto");

      return {
        institution,
        totalClp: records.reduce((total, record) => total + record.amountClp, 0),
        recordCount: records.length,
        confidence: records.length === 0 ? "bajo" : confidence,
      };
    })
    .sort((a, b) => b.totalClp - a.totalClp);
}

export function getMonthlySeries(records: SpendingRecord[]) {
  const byPeriod = new Map<string, number>();

  for (const record of records) {
    byPeriod.set(record.period, (byPeriod.get(record.period) ?? 0) + record.amountClp);
  }

  return Array.from(byPeriod.entries())
    .map(([period, amountClp]) => ({ period, amountClp }))
    .sort((a, b) => a.period.localeCompare(b.period));
}

export function getEstimatedFuelRange(amountClp: number) {
  const lowPricePerLiter = 1200;
  const highPricePerLiter = 1600;
  const lowKmPerLiter = 5;
  const highKmPerLiter = 12;

  const litersMin = amountClp / highPricePerLiter;
  const litersMax = amountClp / lowPricePerLiter;

  return {
    litersMin: Math.round(litersMin),
    litersMax: Math.round(litersMax),
    kmMin: Math.round(litersMin * lowKmPerLiter),
    kmMax: Math.round(litersMax * highKmPerLiter),
  };
}
