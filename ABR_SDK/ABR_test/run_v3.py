''' Simulator for ACM Multimedia 2019 Live Video Streaming Challenge
    Author Dan Yang
    Time 2019-01-31
'''
# import the env
import env_v5 as fixed_env
import load_trace as load_trace
# import matplotlib.pyplot as plt
import time as tm
import ABR_v2 as ABR
import os
import numpy as np
import matplotlib.pyplot as plt


def test(user_id):
    # -- Configuration variables --
    # Edit these variables to configure the simulator

    # Change which set of network trace to use: 'fixed' 'low' 'medium' 'high'
    NETWORK_TRACE = 'fixed'

    method = 'rl'

    # Change which set of video trace to use.
    VIDEO_TRACE = 'tecent'

    # Turn on and off logging.  Set to 'True' to create log files.
    # Set to 'False' would speed up the simulator.
    DEBUG = False

    # Control the subdirectory where log files will be stored.
    LOG_FILE_PATH = '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/log/'

    # create result directory
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)

    # -- End Configuration --
    # You shouldn't need to change the rest of the code here.

    network_trace_dir = '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/dataset/new_network_trace/' + NETWORK_TRACE + '/'
    video_trace_prefix = '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/dataset/video_trace2/' + VIDEO_TRACE + '/new_frame_size_'

    # load the trace
    all_cooked_time, all_cooked_bw, all_file_names = load_trace.load_trace(network_trace_dir)
    # random_seed
    random_seed = 2
    count = 0
    trace_count = 1
    FPS = 30
    frame_time_len = 0.033
    reward_all_sum = 0
    run_time = 0
    # init
    # setting one:
    #     1,all_cooked_time : timestamp
    #     2,all_cooked_bw   : throughput
    #     3,all_cooked_rtt  : rtt
    #     4,agent_id        : random_seed
    #     5,logfile_path    : logfile_path
    #     6,VIDEO_SIZE_FILE : Video Size File Path
    #     7,Debug Setting   : Debug
    net_env = fixed_env.Environment(all_cooked_time=all_cooked_time,
                                    all_cooked_bw=all_cooked_bw,
                                    random_seed=random_seed,
                                    logfile_path=LOG_FILE_PATH,
                                    VIDEO_SIZE_FILE=video_trace_prefix,
                                    Debug=DEBUG)

    abr = ABR.Algorithm()
    abr_init = abr.Initial()

    BIT_RATE = [2000.0, 2500.0, 3000.0, 3500.0] #[500.0, 850.0, 1200.0, 1850.0]  # kpbs
    TARGET_BUFFER = [0, 0.033]  # seconds
    # ABR setting
    RESEVOIR = 0.5
    CUSHION = 2

    cnt = 0
    # defalut setting
    last_bit_rate = 0
    bit_rate = 0
    target_buffer = 1
    latency_limit = 4

    # QOE setting
    reward_frame = 0
    reward_all = 0
    BITRATE_PENALTY = 0.9
    SMOOTH_PENALTY = 0.0
    REBUF_PENALTY = 5.0  # 2.5#2.0
    LANTENCY_PENALTY = 0.005
    SKIP_PENALTY = 0.5
    # past_info setting
    past_frame_num = 7500
    S_time_interval = [0] * past_frame_num
    S_send_data_size = [0] * past_frame_num
    S_chunk_len = [0] * past_frame_num
    S_rebuf = [0] * past_frame_num
    S_buffer_size = [0] * past_frame_num
    S_end_delay = [0] * past_frame_num
    S_chunk_size = [0] * past_frame_num
    S_play_time_len = [0] * past_frame_num
    S_decision_flag = [0] * past_frame_num
    S_buffer_flag = [0] * past_frame_num
    S_cdn_flag = [0] * past_frame_num
    S_skip_time = [0] * past_frame_num
    # params setting
    call_time_sum = 0
    reward_gop = 0

    # frame_index = []
    # bitrate_decision = []
    # rebuf_time = []
    # reward = []
    trace_idx = net_env.get_trace_id()
    log_rate = open(
        '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_bitratevstime_trace' + str(
            net_env.get_trace_id()), 'wb')
    log_rebuf = open(
        '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rebufvstime_trace' + str(
            net_env.get_trace_id()), 'wb')
    log_rebuf2 = open(
        '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rebufvsgop_trace' + str(
            net_env.get_trace_id()), 'wb')
    log_reward = open(
        '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rewardvsgop_trace' + str(
            net_env.get_trace_id()), 'wb')
    #log_rebuf_frame = open(
    #    '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/learning_based_fixed_rebuf_frame_trace' + str(
    #        net_env.get_trace_id()), 'wb')

    while True:

        reward_frame = 0
        # input the train steps
        # if cnt > 5000:
        # plt.ioff()
        #    break
        # actions bit_rate  target_buffer
        # every steps to call the environment
        # time           : physical time
        # time_interval  : time duration in this step
        # send_data_size : download frame data size in this step
        # chunk_len      : frame time len
        # rebuf          : rebuf time in this step
        # buffer_size    : current client buffer_size in this step
        # rtt            : current buffer  in this step
        # play_time_len  : played time len  in this step
        # end_delay      : end to end latency which means the (upload end timestamp - play end timestamp)
        # decision_flag  : Only in decision_flag is True ,you can choose the new actions, other time can't Becasuse the Gop is consist by the I frame and P frame. Only in I frame you can skip your frame
        # buffer_flag    : If the True which means the video is rebuffing , client buffer is rebuffing, no play the video
        # cdn_flag       : If the True cdn has no frame to get
        # end_of_video   : If the True ,which means the video is over.
        time, time_interval, send_data_size, chunk_len, \
        rebuf, buffer_size, play_time_len, end_delay, \
        cdn_newest_id, download_id, cdn_has_frame, skip_frame_time_len, decision_flag, \
        buffer_flag, cdn_flag, skip_flag, end_of_video = net_env.get_video_frame(bit_rate, target_buffer, latency_limit)
        # S_info is sequential order
        S_time_interval.pop(0)
        S_send_data_size.pop(0)
        S_chunk_len.pop(0)
        S_buffer_size.pop(0)
        S_rebuf.pop(0)
        S_end_delay.pop(0)
        S_play_time_len.pop(0)
        S_decision_flag.pop(0)
        S_buffer_flag.pop(0)
        S_cdn_flag.pop(0)
        S_skip_time.pop(0)

        S_time_interval.append(time_interval)
        S_send_data_size.append(send_data_size)
        S_chunk_len.append(chunk_len)
        S_buffer_size.append(buffer_size)
        S_rebuf.append(rebuf)
        S_end_delay.append(end_delay)
        S_play_time_len.append(play_time_len)
        S_decision_flag.append(decision_flag)
        S_buffer_flag.append(buffer_flag)
        S_cdn_flag.append(cdn_flag)
        S_skip_time.append(skip_frame_time_len)
        #log_rebuf_frame.write(str(time) + '\t' + str(rebuf) + '\n')
        #log_rebuf_frame.flush()

        # QOE setting
        if end_delay <= 1.0:
            LANTENCY_PENALTY = 0.005
        else:
            LANTENCY_PENALTY = 0.01

        if not cdn_flag:
            reward_frame = BITRATE_PENALTY * frame_time_len * float(BIT_RATE[
                                                      bit_rate]) / 1000 - REBUF_PENALTY * rebuf  # - LANTENCY_PENALTY  * end_delay - SKIP_PENALTY * skip_frame_time_len
            reward_gop += reward_frame
        else:
            reward_frame = -(REBUF_PENALTY * rebuf)
            reward_gop += reward_frame
        if decision_flag or end_of_video:
            # reward formate = play_time * BIT_RATE - 4.3 * rebuf - 1.2 * end_delay
            reward_frame += -1 * SMOOTH_PENALTY * (abs(BIT_RATE[bit_rate] - BIT_RATE[last_bit_rate]) / 1000)

            if abs(BIT_RATE[bit_rate] - BIT_RATE[last_bit_rate]) / 1000 >= 1.0:
                SMOOTH_PENALTY += 0

            elif abs(BIT_RATE[bit_rate] - BIT_RATE[last_bit_rate]) / 1000 < 1.0 and SMOOTH_PENALTY > 0.1:
                SMOOTH_PENALTY -= 0

            if np.sum(S_rebuf[-61:-1]) >= 1 and REBUF_PENALTY <= 7.0:
                REBUF_PENALTY += 0.1
            elif np.sum(S_rebuf[-61:-1]) < 1 and REBUF_PENALTY > 0.1:
                REBUF_PENALTY -= 0.1

            reward_gop += reward_frame
            log_rate.write(str(time) + '\t' + str(BIT_RATE[bit_rate]) + '\n')
            log_rate.flush()
            log_reward.write(str(cnt) + '\t' + str(reward_gop) + '\n')
            log_reward.flush()
            log_rebuf.write(str(time) + '\t' + str(np.sum(S_rebuf[-31:-1])/30) + '\n')
            log_rebuf.flush()
            log_rebuf2.write(str(cnt) + '\t' + str(np.sum(S_rebuf[-31:-1])/30) + '\n')
            log_rebuf2.flush()
            reward_gop = 0
            # frame_index.append(cnt)
            # bitrate_decision.append(BIT_RATE[bit_rate])
            # rebuf_time.append(np.sum(S_rebuf[-51:-1]))
            # reward.append(reward_frame)
            # last_bit_rate
            last_bit_rate = bit_rate

            # ----------------- Your Algorithm ---------------------
            # which part is the algorithm part ,the buffer based ,
            # if the buffer is enough ,choose the high quality
            # if the buffer is danger, choose the low  quality
            # if there is no rebuf ,choose the low target_buffer
            cnt += 1
            timestamp_start = tm.time()
            bit_rate, target_buffer, latency_limit = abr.run(time,
                                                             S_time_interval,
                                                             S_send_data_size,
                                                             S_chunk_len,
                                                             S_rebuf,
                                                             S_buffer_size,
                                                             S_play_time_len,
                                                             S_end_delay,
                                                             S_decision_flag,
                                                             S_buffer_flag,
                                                             S_cdn_flag,
                                                             S_skip_time,
                                                             end_of_video,
                                                             cdn_newest_id,
                                                             download_id,
                                                             cdn_has_frame,
                                                             abr_init)
            timestamp_end = tm.time()
            call_time_sum += timestamp_end - timestamp_start
            # -------------------- End --------------------------------

        if end_of_video:
            print("network traceID, network_reward, avg_running_time", net_env.get_trace_id(), reward_all,
                  call_time_sum / cnt)
            reward_all_sum += reward_all
            run_time += call_time_sum / cnt
            if trace_count >= len(all_file_names):
                break
            trace_count += 1
            cnt = 0

            call_time_sum = 0
            last_bit_rate = 0
            reward_all = 0
            bit_rate = 0
            target_buffer = 0

            S_time_interval = [0] * past_frame_num
            S_send_data_size = [0] * past_frame_num
            S_chunk_len = [0] * past_frame_num
            S_rebuf = [0] * past_frame_num
            S_buffer_size = [0] * past_frame_num
            S_end_delay = [0] * past_frame_num
            S_chunk_size = [0] * past_frame_num
            S_play_time_len = [0] * past_frame_num
            S_decision_flag = [0] * past_frame_num
            S_buffer_flag = [0] * past_frame_num
            S_cdn_flag = [0] * past_frame_num

            log_rate = open(
                '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_bitratevstime_trace' + str(
                    net_env.get_trace_id()), 'wb')
            log_rebuf = open(
                '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rebufvstime_trace' + str(
                    net_env.get_trace_id()), 'wb')
            log_rebuf2 = open(
                '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rebufvsgop_trace' + str(
                    net_env.get_trace_id()), 'wb')
            log_reward = open(
                '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/reward_' + method + '_' + NETWORK_TRACE + '_rewardvsgop_trace' + str(
                    net_env.get_trace_id()), 'wb')
            #log_rebuf_frame = open(
            #    '/home/jiangzhiqian/Live-Video-Streaming-Challenge-master-tecent/test/learning_based_fixed_rebuf_frame_trace' + str(
            #        net_env.get_trace_id()), 'wb')

        reward_all += reward_frame

    return [reward_all_sum / trace_count, run_time / trace_count]


a = test("aaa")
print(a)
