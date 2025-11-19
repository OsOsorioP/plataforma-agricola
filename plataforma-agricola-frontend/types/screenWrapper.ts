import { ViewStyle } from "react-native"

export type ScreenWrapperProps = {
    style?: ViewStyle;
    children: React.ReactNode;
    isModal?: boolean;
    showPattern?: boolean;
    bgOpacity?: number;
}