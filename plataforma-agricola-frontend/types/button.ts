import { PressableProps, ViewStyle } from "react-native";

export interface buttonProps extends PressableProps{
    style?: ViewStyle ;
    onPress?: () => void;
    children: React.ReactNode
    loading?: boolean
}