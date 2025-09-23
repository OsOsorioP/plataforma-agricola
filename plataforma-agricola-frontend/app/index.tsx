import { Text } from "@react-navigation/elements";
import { Link } from "expo-router";
import { View, StyleSheet } from "react-native";

export default function HomeScreen() {
    return (
        <View style={styles.container}>
            <Text>
                Hola
            </Text>
            <Link href="/(auth)/signin/index">Navigate to nested route</Link>
        </View>
    )
}

const styles = StyleSheet.create({
    container:{
        flex:1,
        alignItems: 'center',
        justifyContent: 'center',
    }
})