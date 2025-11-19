import { Pressable, StyleSheet } from 'react-native'
import React from 'react'
import { colors } from '@/constants/theme'
import { BackButtonProps } from '@/types/components'
import { useRouter } from 'expo-router'
import Ionicons from '@expo/vector-icons/Ionicons'
import { verticalScale } from '@/utils/styling'

export default function BackButton({
    style,
    iconSize = 26,
    color = colors.white
}: BackButtonProps) {
    const router = useRouter()
    return (
        <Pressable 
        onPress={()=> router.back()}
        style={[styles.button, style]}
        >
            <Ionicons name={'arrow-undo-sharp'} size={verticalScale(iconSize)} color={color} />
        </Pressable>
    )
}

const styles = StyleSheet.create({
    button:{

    }
})