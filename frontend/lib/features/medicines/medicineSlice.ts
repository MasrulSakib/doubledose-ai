import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { Medicine } from "@/types/medicine";

type MedicineState = {
  selectedMedicines: Medicine[];
};

const initialState: MedicineState = {
  selectedMedicines: [],
};

const medicineSlice = createSlice({
  name: "medicines",
  initialState,
  reducers: {
    addMedicine(state, action: PayloadAction<Medicine>) {
      const medicine = action.payload;

      const alreadySelected = state.selectedMedicines.some(
        (item) => item.id === medicine.id,
      );

      if (alreadySelected || state.selectedMedicines.length >= 5) {
        return;
      }

      state.selectedMedicines.push(medicine);
    },

    removeMedicine(state, action: PayloadAction<number>) {
      state.selectedMedicines = state.selectedMedicines.filter(
        (medicine) => medicine.id !== action.payload,
      );
    },

    clearMedicines(state) {
      state.selectedMedicines = [];
    },
  },
});

export const { addMedicine, removeMedicine, clearMedicines } =
  medicineSlice.actions;

export default medicineSlice.reducer;
