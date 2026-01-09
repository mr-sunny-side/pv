#include<stdio.h>
#include<stdlib.h>
#include<stdint.h>
#include<string.h>

#pragma pack(push, 1)
typedef struct {
    uint16_t file_type;
    uint32_t file_size;
    uint16_t reserved1;
    uint16_t reserved2;
    uint32_t offset_data;
} BmpFileHeader;

typedef struct {
    uint32_t header_size;
    int32_t  width;
    int32_t  height;
    uint16_t planes;
    uint16_t bits_per_pixel;
    uint32_t compression;
    uint32_t image_size;
    int32_t  x_pixels_per_meter;
    int32_t  y_pixels_per_meter;
    uint32_t colors_used;
    uint32_t colors_important;
} BmpInfoHeader;
#pragma pack(pop)

// RGBピクセル構造体
typedef struct {
    uint8_t blue;
    uint8_t green;
    uint8_t red;
} Pixel;

// 特定座標のピクセルを取得
int get_pixel(FILE *fp, const BmpFileHeader *fh, const BmpInfoHeader *ih,
              int x, int y, Pixel *pixel)
{
    // 範囲チェック
    if (x < 0 || x >= ih->width || y < 0 || y >= ih->height) {
        fprintf(stderr, "Error: Coordinates out of range\n");
        return -1;
    }

    // 計算
    int bytes_per_pixel = ih->bits_per_pixel / 8;
    int row_size = ih->width * bytes_per_pixel;
    int padding = (4 - (row_size % 4)) % 4;
    int padded_row_size = row_size + padding;

    // Y軸を反転（BMPは下から上へ）
    int inverted_y = ih->height - 1 - y;

    // ファイル内の位置
    long offset = fh->offset_data +
                  inverted_y * padded_row_size +
                  x * bytes_per_pixel;

    // その位置にシーク
    if (fseek(fp, offset, SEEK_SET) != 0) {
        fprintf(stderr, "Error: Cannot seek to pixel data\n");
        return -1;
    }

    // ピクセルを読み込む（BGR順）
    if (fread(pixel, sizeof(Pixel), 1, fp) != 1) {
        fprintf(stderr, "Error: Cannot read pixel data\n");
        return -1;
    }

    return 0;
}

// すべてのピクセルを表示
void print_all_pixels(FILE *fp, const BmpFileHeader *fh, const BmpInfoHeader *ih)
{
    Pixel pixel;

    printf("=== All Pixels ===\n");
    // 上から下へ表示（Y軸を反転）
    for (int y = ih->height - 1; y >= 0; y--) {
        for (int x = 0; x < ih->width; x++) {
            if (get_pixel(fp, fh, ih, x, y, &pixel) == 0) {
                printf("(%d,%d): R=%3d G=%3d B=%3d  ",
                       x, y, pixel.red, pixel.green, pixel.blue);
            }
        }
        printf("\n");
    }
}

int main(int argc, char *argv[])
{
    FILE *fp;
    BmpFileHeader file_header;
    BmpInfoHeader info_header;
    Pixel pixel;
    int x, y;

    // 引数チェック
    if (argc < 2) {
        fprintf(stderr, "Usage:%s <bmp_file> [x y | --all]\n", argv[0]);
        return 1;
    }

    // ファイルを開く
    fp = fopen(argv[1], "rb");
    if (fp == NULL) {
        fprintf(stderr, "Error: Cannot open file '%s'\n", argv[1]);
        return 1;
    }

    // ヘッダーを読み込む
    if (fread(&file_header, sizeof(BmpFileHeader), 1, fp) != 1 ||
        fread(&info_header, sizeof(BmpInfoHeader), 1, fp) != 1) {
        fprintf(stderr, "Error: Cannot read headers\n");
        fclose(fp);
        return 1;
    }

    // BMPファイルかチェック
    if (file_header.file_type != 0x4D42) {
        fprintf(stderr, "Error: Not a BMP file\n");
        fclose(fp);
        return 1;
    }

    // 24ビットBMPのみサポート
    if (info_header.bits_per_pixel != 24) {
        fprintf(stderr, "Error: Only 24-bit BMP is supported\n");
        fclose(fp);
        return 1;
    }

    // モード判定
    if (argc >= 3 && strcmp(argv[2], "--all") == 0) {
        // すべてのピクセルを表示
        print_all_pixels(fp, &file_header, &info_header);
    } else if (argc >= 4) {
        // 特定座標のピクセルを表示
        x = atoi(argv[2]);
        y = atoi(argv[3]);

        if (get_pixel(fp, &file_header, &info_header, x, y, &pixel) == 0) {
            printf("Pixel at (%d,%d):\n", x, y);
            printf("  Red:%3d (0x%02X)\n", pixel.red, pixel.red);
            printf("  Green:%3d (0x%02X)\n", pixel.green, pixel.green);
            printf("  Blue:%3d (0x%02X)\n", pixel.blue, pixel.blue);
        } else {
            fclose(fp);
            return 1;
        }
    } else {
        fprintf(stderr, "Usage:%s <bmp_file> [x y | --all]\n", argv[0]);
        fclose(fp);
        return 1;
    }

    fclose(fp);
    return 0;
}
