import { StyleSheet, View } from 'react-native'
import React from 'react'
import { MessageProps } from '@/types/components'
import { useAuth } from '@/context/AuthContext'
import { scale, verticalScale } from '@/utils/styling'
import { colors, spacingX, spacingY } from '@/constants/theme'
import Typo from '../ui/Typo'
import { Image } from 'expo-image'
import { getFileFromBase64 } from '@/utils/base64'
import Markdown from 'react-native-markdown-display';

export default function MessageItem({
    item
}: { item: MessageProps }) {
    const { user: currentUser } = useAuth()
    const isMe = item.isMe

    return (
        <View
            style={[
                styles.messageContainer,
                isMe ? styles.myMessage : styles.theirMessage
            ]}
        >
            {
                !isMe && (
                    <></>
                )
            }
            <View
                style={[
                    styles.messageBubble,
                    isMe ? styles.myBubble : styles.theirBubble
                ]}
            >
                {!isMe && (
                    <Typo color={colors.neutral200} fontWeight={"600"} size={13}>
                        Agrosmi
                    </Typo>
                )}
                {item.attachement && (<Image source={{ uri: `data:image/jpeg;base64,${item.attachement}` }} contentFit='cover' style={styles.attachment} transition={100} />)}
                {item.content && (<Typo size={15}><Markdown>{item.content}</Markdown></Typo>)}
            </View>
        </View>
    )
}

const styles = StyleSheet.create({
    messageContainer: {
        flexDirection: "row",
        gap: spacingX._7,
        maxWidth: "100%",
    },
    myMessage: {
        alignItems: "flex-end"
    },
    theirMessage: {
        alignItems: "flex-start"
    },
    messageAvatar: {
        alignSelf: "flex-end",
    },
    attachment: {
        height: verticalScale(180),
        width: verticalScale(180),
        borderRadius: scale(10),
    },
    messageBubble: {
        padding: spacingX._10,
        borderRadius: scale(15),
        gap: spacingY._5,
    },
    myBubble: {
        backgroundColor: colors.white,
    },
    theirBubble: {
        backgroundColor: colors.green
    },
})