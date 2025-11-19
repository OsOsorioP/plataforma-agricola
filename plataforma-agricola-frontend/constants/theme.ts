import { scale, verticalScale } from "@/utils/styling";

export const colors = {
  primary: "#1dfa15ff",
  primaryLight: "#8afe8eff",
  primaryDark: "#08ea3dff",
  text: "#292524",
  background: "#ffffff",
  black: "#000",
  white: "#fff",
  green: "#16a34a",
  red: "#a31616ff",
  neutral50: "#fafaf9",
  neutral100: "#f5f5f4",
  neutral200: "#e7e5e4",
  neutral300: "#d6d3d1",
  neutral350: "#cccccc",
  neutral400: "#a8a29e",
};

export const spacingX = {
  _3: scale(3),
  _5: scale(3),
  _7: scale(3),
  _9: scale(9),
  _10: scale(10),
  _12: scale(12),
  _15: scale(15),
  _20: scale(20),
  _25: scale(25),
  _30: scale(30),
  _35: scale(35),
  _40: scale(40),
};

export const spacingY = {
  _3: verticalScale(3),
  _5: verticalScale(5),
  _7: verticalScale(7),
  _9: verticalScale(9),
  _10: verticalScale(10),
  _12: verticalScale(12),
  _15: verticalScale(15),
  _20: verticalScale(20),
  _25: verticalScale(25),
  _30: verticalScale(30),
  _35: verticalScale(35),
  _40: verticalScale(40),
  _50: verticalScale(50),
  _60: verticalScale(60),
};

export const radius = {
  full: scale(100),
};
