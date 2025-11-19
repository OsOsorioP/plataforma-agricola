import { StyleSheet, View } from 'react-native'
import React from 'react'
import ScreenWrapper from '@/components/layout/ScreenWrapper'
import Typo from '@/components/ui/Typo'
import { colors, spacingX, spacingY } from '@/constants/theme'
import { verticalScale } from '@/utils/styling'
import Animated, { FadeIn } from 'react-native-reanimated'
import Button from '@/components/ui/Button'
import { useRouter } from 'expo-router'

export default function WelcomeScreen() {
    const router = useRouter()

    return (
        <ScreenWrapper showPattern={true} bgOpacity={0.2}>
            <View style={styles.container}>
                <View style={{ alignItems: "center" }}>
                    <Typo
                        color={colors.white}
                        size={43}
                        fontWeight={"900"}
                    >
                        Agrosmi
                    </Typo>
                </View>
                <Animated.Image
                    entering={FadeIn.duration(700).springify()}
                    source={require("@/assets/images/logo.png")}
                    style={styles.welcomeImage}
                    resizeMode={"contain"}
                />
                <View>
                    <Typo color={colors.white} size={33} fontWeight={"800"}>
                        Bienvenido
                    </Typo>
                    <Typo color={colors.white} size={33} fontWeight={"800"}>
                        a la mejor plataforma
                    </Typo>
                    <Typo color={colors.white} size={33} fontWeight={"800"}>
                        sobre agricultura sostenible
                    </Typo>
                </View>
                <Button
                    style={{ backgroundColor: colors.white }}
                    onPress={() => router.push("/(auth)/register")}
                >
                    <Typo size={23} fontWeight={"bold"}>
                        Comenzar
                    </Typo>
                </Button>
            </View>
        </ScreenWrapper>
    )
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: "space-around",
        paddingHorizontal: spacingX._20,
        marginVertical: spacingY._10
    },
    backgound: {
        flex: 1,
        backgroundColor: colors.neutral400
    },
    welcomeImage: {
        height: verticalScale(260),
        aspectRatio: 1,
        alignSelf: "center"
    }
})