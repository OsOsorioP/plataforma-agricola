import {
  TextInput,
  TextInputProps,
  TextProps,
  TextStyle,
  ViewStyle,
} from "react-native";

export type TypoProps = {
  size?: number;
  color?: string;
  fontWeight?: TextStyle["fontWeight"];
  children: any | null;
  style?: TextStyle;
  textProps?: TextProps;
};

export type BackButtonProps = {
  style?: ViewStyle;
  color?: string;
  iconSize?: number;
};

export interface InputProps extends TextInputProps {
  icon?: React.ReactNode;
  containerStyle?: ViewStyle;
  inputStyle?: TextStyle;
  inputRef?: React.RefObject<TextInput>;
  // label?: string;
  // error?: string;
}

export type HeaderProps = {
  title?: string;
  style?: ViewStyle;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
};

export type MessageProps = {
  id: string | undefined;
  sender: 'ai' | 'user';
  content: string;
  isMe: boolean;
  attachement?: string | null | undefined;
};
