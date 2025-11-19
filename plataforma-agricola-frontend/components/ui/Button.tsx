import { StyleSheet, View, Pressable } from 'react-native';
import { buttonProps } from '@/types/button';
import Loading from '@/components/ui/Loading';
import { colors, radius } from '@/constants/theme';

export default function Button({ style, onPress, children, loading = false }: buttonProps) {
    if (loading) {
        return (
            <View style={[styles.button, style, { backgroundColor: "transparent" }]}>
                <Loading />
            </View>
        );
    };

    return (
        <Pressable style={[styles.button, style]} onPress={onPress}>
            {children}
        </Pressable>
    );
}

const styles = StyleSheet.create({
    button: {
        backgroundColor: colors.primary,
        borderRadius: radius.full,
        borderCurve: 'continuous',
        height: 56,
        justifyContent: 'center',
        alignItems: 'center'
    }
});