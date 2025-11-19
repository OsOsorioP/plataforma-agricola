import { View, Platform, Dimensions, StatusBar } from 'react-native'
import React from 'react'
import { ScreenWrapperProps } from '@/types/screenWrapper'
import { ImageBackground } from 'expo-image';
import { colors } from '@/constants/theme';

const { height } = Dimensions.get('window')

export default function ScreenWrapper({
    style,
    children,
    showPattern = false,
    isModal = false,
    bgOpacity = 0.1,
}: ScreenWrapperProps) {
    let paddingTop = Platform.OS === 'ios' ? height * 0.06 : 0;
    let paddingBottom = 0

    if (isModal) {
        paddingTop = Platform.OS === 'ios' ? height * 0.02 : 0;
        paddingBottom = height * 0.02;
    }

    return (
        <ImageBackground
            style={{ flex: 1, backgroundColor: isModal ? colors.white : colors.black }}
            imageStyle={{ opacity: showPattern ? bgOpacity : 0 }}
            source={require('@/assets/images/wrapper.png')}
        >
            <View
                style={[{ paddingTop, paddingBottom, flex: 1, }, style]}
            >
                <StatusBar barStyle={'light-content'} backgroundColor={'transparent'} />
                {children}
            </View>
        </ImageBackground>
    )
}