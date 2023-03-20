#!/bin/bash

set -e
this_dir=$(dirname "$0")
for arch in "x86_64" "arm64"; do
    swift build -c release --arch $arch --package-path "$this_dir/Sources/appkit-launcher"
    cp $(swift build -c release --arch $arch --package-path "$this_dir/Sources/appkit-launcher" --show-bin-path)/appkit-launcher "$this_dir/../../menuinst/data/appkit_launcher_$arch"
done

cp "$this_dir/../../menuinst/data/appkit_launcher_arm64" ~/Applications/FileTypeAssociation.app/Contents/MacOS/filetypeassociation
