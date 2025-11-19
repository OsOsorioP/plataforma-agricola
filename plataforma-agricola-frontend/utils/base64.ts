export function getFileFromBase64(base64:string){
    let img = new Image()
    img.src = base64
    return img
}