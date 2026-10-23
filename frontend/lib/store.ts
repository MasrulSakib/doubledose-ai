import { configureStore } from "@reduxjs/toolkit";

import medicineReducer from "@/lib/features/medicines/medicineSlice";

export const makeStore = () =>
  configureStore({
    reducer: {
      medicines: medicineReducer,
    },
  });

export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];
