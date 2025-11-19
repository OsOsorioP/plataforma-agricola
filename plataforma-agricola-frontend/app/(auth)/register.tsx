import { KeyboardAvoidingView, Platform, StyleSheet, View, ScrollView, Pressable, Alert } from 'react-native'
import React, { useRef, useState } from 'react'
import ScreenWrapper from '@/components/layout/ScreenWrapper'
import Typo from '@/components/ui/Typo'
import { colors, spacingX, spacingY } from '@/constants/theme'
import BackButton from '@/components/ui/BackButton'
import Input from '@/components/ui/Input'
import Ionicons from '@expo/vector-icons/Ionicons'
import { scale, verticalScale } from '@/utils/styling'
import Button from '@/components/ui/Button'
import { useRouter } from 'expo-router'
import { useAuth } from '@/context/AuthContext'

export default function RegisterScreen() {
    const nameRef = useRef("")
    const emailRef = useRef("")
    const passwordRef = useRef("")
    const [isLoading, setIsLoading] = useState(false)
    const router = useRouter()

    const { signUp } = useAuth()

    const handleSumit = async () => {
        if (!emailRef.current || !passwordRef.current || !nameRef.current) {
            Alert.alert("Sign In", "Please fill all the fields");
            return;
        }
        try {
            setIsLoading(true)
            await signUp(emailRef.current, passwordRef.current, nameRef.current)
        } catch (error: any) {
            Alert.alert("Register Error", error.message)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <KeyboardAvoidingView
            style={{ flex: 1 }}
            behavior={Platform.OS === 'ios' ? "padding" : "height"}
        >
            <ScreenWrapper showPattern={true} bgOpacity={0.3}>
                <View style={styles.container}>
                    <View style={styles.header}>
                        <BackButton iconSize={28} />
                        <Typo size={17} color={colors.white}>¿Necesitas ayuda?</Typo>
                    </View>
                    <View style={styles.content}>
                        <ScrollView
                            contentContainerStyle={styles.form}
                            showsVerticalScrollIndicator={false}
                        >
                            <View style={{ gap: spacingY._10, marginBottom: spacingY._15 }}>
                                <Typo size={28} fontWeight={"600"}>
                                    Primeros pasos
                                </Typo>
                                <Typo color={colors.neutral400}>
                                    Crea una cuenta para continuar
                                </Typo>
                            </View>
                            <Input
                                placeholder='Ingresa tu nombre'
                                onChangeText={(value: string) => nameRef.current = value}
                                icon={<Ionicons name={'person-sharp'} size={verticalScale(26)} color={colors.neutral400} />}
                            />
                            <Input
                                placeholder='Ingresa tu correo'
                                onChangeText={(value: string) => emailRef.current = value}
                                icon={<Ionicons name={'mail-sharp'} size={verticalScale(26)} color={colors.neutral400} />}
                            />
                            <Input
                                placeholder='Ingresa tu contraseña'
                                secureTextEntry
                                onChangeText={(value: string) => passwordRef.current = value}
                                icon={<Ionicons name={'lock-closed-sharp'} size={verticalScale(26)} color={colors.neutral400} />}
                            />
                            <View style={{ marginTop: spacingY._25, gap: spacingY._15 }}>
                                <Button loading={isLoading} onPress={handleSumit}>
                                    <Typo fontWeight={"bold"} color={colors.black} size={20}>
                                        Inscribirse
                                    </Typo>
                                </Button>
                                <View style={styles.footer}>
                                    <Typo>
                                        ¿Ya tienes una cuenta?
                                    </Typo>
                                    <Pressable onPress={() => router.push("/(auth)/login")}>
                                        <Typo fontWeight={"bold"} color={colors.primaryDark}>
                                            Inicia
                                        </Typo>
                                    </Pressable>
                                </View>
                            </View>
                        </ScrollView>
                    </View>
                </View>
            </ScreenWrapper>
        </KeyboardAvoidingView>
    )
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        //gap: spacingY._30,
        //marginHorizontal: spacingX._20,
        justifyContent: "space-between",
    },
    header: {
        paddingHorizontal: spacingX._20,
        paddingTop: spacingY._15,
        paddingBottom: spacingY._25,
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
    },
    content: {
        flex: 1,
        backgroundColor: colors.white,
        borderTopLeftRadius: scale(50),
        borderTopRightRadius: scale(50),
        borderCurve: "continuous",
        paddingHorizontal: spacingX._20,
        paddingTop: spacingY._20,
    },
    form: {
        gap: spacingY._15,
        marginTop: spacingY._20,
    },
    footer: {
        flexDirection: "row",
        justifyContent: "center",
        alignItems: "center",
        gap: 5
    }
})