import type { Medicine } from "@/types/medicine";

type MedicineCardProps = {
  medicine: Medicine;
  onRemove?: (medicineId: number) => void;
  onSelect?: (medicine: Medicine) => void;
  selected?: boolean;
  disabled?: boolean;
};

export default function MedicineCard({
  medicine,
  onRemove,
  onSelect,
  selected = false,
  disabled = false,
}: MedicineCardProps) {
  const genericName = medicine.generic_name?.trim();
  const sourceName = medicine.source_display_name?.trim();

  return (
    <article className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-emerald-200 hover:shadow-md">
      <div className="min-w-0 flex-1">
        <h3 className="break-words text-sm font-semibold text-slate-900">
          {medicine.brand_name}
        </h3>
        {genericName && (
          <p className="mt-1 break-words text-sm text-slate-600">
            {genericName}
          </p>
        )}
        {sourceName && (
          <p className="mt-2 break-words text-xs leading-5 text-slate-400">
            {sourceName}
          </p>
        )}
      </div>

      {onRemove && (
        <button
          type="button"
          onClick={() => onRemove(medicine.id)}
          className="shrink-0 rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50"
          aria-label={`Remove ${medicine.brand_name}`}
        >
          Remove
        </button>
      )}

      {onSelect && (
        <button
          type="button"
          onClick={() => onSelect(medicine)}
          disabled={disabled || selected}
          className="shrink-0 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {selected ? "Added" : "Add"}
        </button>
      )}
    </article>
  );
}
