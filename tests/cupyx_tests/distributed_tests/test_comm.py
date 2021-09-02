import time
import unittest

import cupy
from cupy import cuda
from cupy.cuda import nccl
from cupy import testing

from cupyx.distributed import NCCLBackend
from cupyx.distributed._store import ExceptionAwareProcess

nccl_available = nccl.available

if nccl_available:
    nccl_version = nccl.get_version()
else:
    nccl_version = -1

N_WORKERS = 2


@unittest.skipUnless(nccl_available, 'nccl is not installed')
class TestNCCLBackend(unittest.TestCase):
    def _launch_workers(self, n_workers, func, args=()):
        processes = []
        # TODO catch exceptions
        for rank in range(n_workers):
            p = ExceptionAwareProcess(
                target=func,
                args=(rank, n_workers) + args)
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

    @testing.for_all_dtypes(no_bool=True)
    def test_broadcast(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_broadcast(rank, n_workers, root, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            expected = cupy.arange(2 * 3 * 4, dtype=dtype).reshape((2, 3, 4))
            if rank == root:
                in_array = expected
            else:
                in_array = cupy.zeros((2, 3, 4), dtype=dtype)

            comm.broadcast(in_array, root)
            testing.assert_allclose(in_array, expected)

        self._launch_workers(N_WORKERS, run_broadcast, (0, dtype))
        self._launch_workers(N_WORKERS, run_broadcast, (1, dtype))

    @testing.for_all_dtypes(no_bool=True)
    def test_reduce(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_reduce(rank, n_workers, root, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = cupy.arange(2 * 3 * 4, dtype='f').reshape(2, 3, 4)
            out_array = cupy.zeros((2, 3, 4), dtype='f')
            comm.reduce(in_array, out_array, root)
            if rank == root:
                testing.assert_allclose(out_array, 2 * in_array)

        self._launch_workers(N_WORKERS, run_reduce, (0, dtype))
        self._launch_workers(N_WORKERS, run_reduce, (1, dtype))

    @testing.for_all_dtypes(no_bool=True)
    def test_all_reduce(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_all_reduce(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = cupy.arange(2 * 3 * 4, dtype='f').reshape(2, 3, 4)
            out_array = cupy.zeros((2, 3, 4), dtype='f')

            comm.all_reduce(in_array, out_array)
            testing.assert_allclose(out_array, 2 * in_array)

        self._launch_workers(N_WORKERS, run_all_reduce, (dtype,))

    @testing.for_all_dtypes(no_bool=True)
    def test_reduce_scatter(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_reduce_scatter(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = 1 + cupy.arange(
                n_workers * 10, dtype='f').reshape(n_workers, 10)
            out_array = cupy.zeros((10,), dtype='f')

            comm.reduce_scatter(in_array, out_array, 10)
            testing.assert_allclose(out_array, 2 * in_array[rank])

        self._launch_workers(N_WORKERS, run_reduce_scatter, (dtype,))

    @testing.for_all_dtypes(no_bool=True)
    def test_all_gather(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_all_gather(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = (rank + 1) * cupy.arange(
                n_workers * 10, dtype='f').reshape(n_workers, 10)
            out_array = cupy.zeros((n_workers, 10), dtype='f')
            comm.all_gather(in_array, out_array, 10)
            expected = 1 + cupy.arange(n_workers).reshape(n_workers, 1)
            expected = expected * cupy.broadcast_to(
                cupy.arange(10, dtype='f'), (n_workers, 10))
            testing.assert_allclose(out_array, expected)

        self._launch_workers(N_WORKERS, run_all_gather, (dtype,))

    @testing.for_all_dtypes(no_bool=True)
    def test_send_and_recv(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_send_and_recv(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = cupy.arange(10, dtype='f')
            out_array = cupy.zeros((10,), dtype='f')
            if rank == 0:
                comm.send(in_array, 1)
            else:
                comm.recv(out_array, 0)
                testing.assert_allclose(out_array, in_array)

        self._launch_workers(N_WORKERS, run_send_and_recv, (dtype,))

    @testing.for_all_dtypes(no_bool=True)
    def test_send_recv(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_send_recv(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = cupy.arange(10, dtype='f')
            for i in range(n_workers):
                out_array = cupy.zeros((10,), dtype='f')
                comm.send_recv(in_array, out_array, i)
                testing.assert_allclose(out_array, in_array)

        self._launch_workers(N_WORKERS, run_send_recv, (dtype,))

    @testing.for_all_dtypes(no_bool=True)
    def test_scatter(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_scatter(rank, n_workers, root, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = 1 + cupy.arange(
                n_workers * 10, dtype='f').reshape(n_workers, 10)
            out_array = cupy.zeros((10,), dtype='f')

            comm.scatter(in_array, out_array, root)
            if rank > 0:
                testing.assert_allclose(out_array, in_array[rank])

        self._launch_workers(N_WORKERS, run_scatter, (0, dtype))
        self._launch_workers(N_WORKERS, run_scatter, (1, dtype))

    @testing.for_all_dtypes(no_bool=True)
    def test_gather(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_gather(rank, n_workers, root, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = (rank + 1) * cupy.arange(10, dtype='f')
            out_array = cupy.zeros((n_workers, 10), dtype='f')
            comm.gather(in_array, out_array, root)
            if rank == root:
                expected = 1 + cupy.arange(n_workers).reshape(n_workers, 1)
                expected = expected * cupy.broadcast_to(
                    cupy.arange(10, dtype='f'), (n_workers, 10))
                testing.assert_allclose(out_array, expected)

        self._launch_workers(N_WORKERS, run_gather, (0, dtype))
        self._launch_workers(N_WORKERS, run_gather, (1, dtype))

    @testing.for_all_dtypes(no_bool=True)
    def test_all_to_all(self, dtype):
        if dtype in (cupy.int16, cupy.uint16):
            return  # nccl does not support int16

        def run_all_to_all(rank, n_workers, dtype):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            in_array = cupy.arange(
                n_workers * 10, dtype='f').reshape(n_workers, 10)
            out_array = cupy.zeros((n_workers, 10), dtype='f')
            comm.all_to_all(in_array, out_array)
            expected = (10 * rank) + cupy.broadcast_to(
                cupy.arange(10, dtype='f'), (n_workers, 10))
            testing.assert_allclose(out_array, expected)

        self._launch_workers(N_WORKERS, run_all_to_all, (dtype,))

    def test_barrier(self):
        def run_barrier(rank, n_workers):
            dev = cuda.Device(rank)
            dev.use()
            comm = NCCLBackend(n_workers, rank)
            comm.barrier()
            before = time.time()
            if rank == 0:
                time.sleep(2)
            comm.barrier()
            after = time.time()
            assert int(after - before) == 2

        self._launch_workers(N_WORKERS, run_barrier)
