import { StatusBar, StyleSheet, View } from 'react-native'
import React, { useEffect } from 'react'
import { colors } from '@/constants/theme'

import Animated, { FadeInDown } from 'react-native-reanimated'
import { useRouter } from 'expo-router'
import Typo from '@/components/ui/Typo'

const SplashScreen = () => {
    const router = useRouter()

    useEffect(() => {
        setTimeout(() => { router.replace('/(auth)/welcome') }, 2000);
    }, [router])

    return (
        <View style={styles.container}>
            <StatusBar barStyle={'light-content'} backgroundColor={colors.background} />
            <Animated.Image
                source={require('@/assets/images/logo.png')}
                entering={FadeInDown.duration(700).springify()}
                style={styles.logo}
                resizeMode={"contain"}
            />
            <Typo>Agrosmi</Typo>
        </View>
    )
}

export default SplashScreen

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: colors.background
    },
    logo: {
        height: '23%',
        aspectRatio: 1,
    }
})