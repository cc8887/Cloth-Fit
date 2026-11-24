#include <igl/read_triangle_mesh.h>
#include <igl/edges.h>
#include <ipc/ipc.hpp>
#include <iostream>

int main(int argc, char** argv)
{
    if (argc != 3) {
        std::cerr << "usage: cloth_validate avatar.obj garment.obj\n";
        return 2;
    }
    Eigen::MatrixXd bv, gv;
    Eigen::MatrixXi bf, gf;
    if (!igl::read_triangle_mesh(argv[1], bv, bf) || !igl::read_triangle_mesh(argv[2], gv, gf) ||
        bv.rows() == 0 || gv.rows() == 0 || bv.cols() != 3 || gv.cols() != 3 ||
        bf.cols() != 3 || gf.cols() != 3 || bf.rows() == 0 || gf.rows() == 0 ||
        !bv.allFinite() || !gv.allFinite()) {
        std::cerr << "Could not load finite triangle meshes.\n";
        return 2;
    }
    Eigen::MatrixXd v(bv.rows() + gv.rows(),3);
    v << bv, gv;
    Eigen::MatrixXi f(bf.rows() + gf.rows(),3), e;
    f << bf, gf.array() + bv.rows();
    igl::edges(f,e);
    const size_t n = bv.rows();
    ipc::CollisionMesh cross(v,e,f);
    cross.can_collide = [n](size_t i, size_t j) { return (i < n) != (j < n); };
    const auto cross_ids = ipc::my_has_intersections(cross,v,ipc::BroadPhaseMethod::BVH);
    Eigen::MatrixXi ge;
    igl::edges(gf,ge);
    ipc::CollisionMesh cloth(gv,ge,gf);
    const auto self_ids = ipc::my_has_intersections(cloth,gv,ipc::BroadPhaseMethod::BVH);
    std::cout << "body_vertices=" << n << " garment_vertices=" << gv.rows()
              << " body_garment_intersection=" << (cross_ids[0]>=0)
              << " garment_self_intersection=" << (self_ids[0]>=0)
              << " static_same_library=IPC\n";
    return cross_ids[0]>=0 || self_ids[0]>=0;
}
