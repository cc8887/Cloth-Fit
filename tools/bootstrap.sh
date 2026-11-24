#!/usr/bin/env bash
# Build on Linux x86_64 in this repository; does not install system packages.
set -euo pipefail
cd "$(dirname "$0")/.."
root="$PWD"
revision=123e2440f46720b5f993c91d1705aff838aa55fb
tbb_revision=9afd759b72c0c233cd5ea3c3c06b0894c9da9c54
if [[ ! -d cloth-fit/.git ]]; then
    git clone https://github.com/Huangzizhou/cloth-fit cloth-fit
fi
git -C cloth-fit checkout --detach "$revision"
if [[ ! -d cloth-tbb/.git ]]; then
    git clone --depth 1 --branch v2021.12.0 https://github.com/oneapi-src/oneTBB cloth-tbb
fi
test "$(git -C cloth-tbb rev-parse HEAD)" = "$tbb_revision"
python3 -m venv cloth-env
cloth-env/bin/python -m pip install 'cmake==3.31.10' 'ninja==1.13.2'
cmake="$root/cloth-env/bin/cmake"
ninja="$root/cloth-env/bin/ninja"
jobs="${JOBS:-2}"
"$cmake" -S cloth-tbb -B cloth-tbb/build -G Ninja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DTBB_TEST=OFF \
    -DCMAKE_INSTALL_PREFIX="$root/cloth-deps" -DCMAKE_MAKE_PROGRAM="$ninja"
"$cmake" --build cloth-tbb/build -j "$jobs"
"$cmake" --install cloth-tbb/build
"$cmake" -S cloth-fit -B cloth-fit/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DPOLYFEM_WITH_TESTS=OFF -DPOLYSOLVE_WITH_CHOLMOD=OFF \
    -DCPM_SOURCE_CACHE="$root/cloth-cache" -DCMAKE_MAKE_PROGRAM="$ninja" \
    -DCMAKE_PREFIX_PATH="$root/cloth-deps" -DOPENVDB_USE_DELAYED_LOADING=OFF \
    -DUSE_BLOSC=OFF -DUSE_ZLIB=OFF -DUSE_IMATH_HALF=OFF -DOPENVDB_BUILD_BINARIES=OFF \
    -DUSE_EXPLICIT_INSTANTIATION=OFF
"$cmake" --build cloth-fit/build --target PolyFEM_bin -j "$jobs"
