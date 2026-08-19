# GRAPH - full dependency table

_Commit `759306c`. Do not read this whole file - grep it._

Roles: CORE (many importers) | ENTRY (start here) | ORCHESTRATOR (imports many) |
LEAF (isolated) | PLUGIN (loaded by name) | RUNTIME-LOADED (observed) | ORPHAN? (unreferenced)

| File | Role | In | Out | Commits | Group |
|---|---|---:|---:|---:|---|
| `facefusion/types.py` | CORE | 103 | 0 | 0 | `facefusion` |
| `facefusion/__init__.py` | CORE | 98 | 0 | 0 | `facefusion` |
| `facefusion/state_manager.py` | CORE | 83 | 3 | 0 | `facefusion` |
| `facefusion/translator.py` | CORE | 67 | 1 | 0 | `facefusion` |
| `facefusion/common_helper.py` | CORE | 62 | 0 | 0 | `facefusion` |
| `facefusion/filesystem.py` | CORE | 61 | 1 | 0 | `facefusion` |
| `facefusion/download.py` | CORE | 41 | 10 | 0 | `facefusion` |
| `facefusion/jobs/job_manager.py` | CORE | 36 | 6 | 0 | `facefusion/jobs` |
| `facefusion/uis/core.py` | CORE | 34 | 13 | 0 | `facefusion/uis` |
| `facefusion/vision.py` | CORE | 29 | 5 | 0 | `facefusion` |
| `facefusion/logger.py` | CORE | 26 | 3 | 0 | `facefusion` |
| `facefusion/choices.py` | CORE | 25 | 2 | 0 | `facefusion` |
| `tests/helper.py` | TEST | 23 | 2 | 0 | `tests` |
| `facefusion/content_analyser.py` | CORE | 20 | 11 | 0 | `facefusion` |
| `facefusion/processors/core.py` | ORCHESTRATOR | 20 | 59 | 0 | `facefusion/processors` |
| `facefusion/inference_manager.py` | CORE | 18 | 12 | 0 | `facefusion` |
| `facefusion/thread_helper.py` | CORE | 18 | 2 | 0 | `facefusion` |
| `facefusion/jobs/job_store.py` | CORE | 15 | 1 | 0 | `facefusion/jobs` |
| `facefusion/face_detector.py` | CORE | 14 | 9 | 0 | `facefusion` |
| `facefusion/face_landmarker.py` | CORE | 14 | 8 | 0 | `facefusion` |
| `facefusion/processors/types.py` | CORE | 14 | 1 | 0 | `facefusion/processors` |
| `facefusion/config.py` | CORE | 13 | 3 | 0 | `facefusion` |
| `facefusion/face_analyser.py` | CORE | 13 | 10 | 0 | `facefusion` |
| `facefusion/face_classifier.py` | CORE | 13 | 7 | 0 | `facefusion` |
| `facefusion/face_helper.py` | CORE | 13 | 1 | 0 | `facefusion` |
| `facefusion/face_recognizer.py` | CORE | 13 | 7 | 0 | `facefusion` |
| `facefusion/program_helper.py` | CORE | 13 | 0 | 0 | `facefusion` |
| `facefusion/uis/types.py` | CORE | 13 | 0 | 0 | `facefusion/uis` |
| `facefusion/video_manager.py` | CORE | 13 | 1 | 0 | `facefusion` |
| `facefusion/face_masker.py` | CORE | 12 | 8 | 0 | `facefusion` |
| `facefusion/process_manager.py` | CORE | 12 | 1 | 0 | `facefusion` |
| `facefusion/execution.py` | CORE | 11 | 3 | 0 | `facefusion` |
| `facefusion/face_selector.py` | CORE | 10 | 4 | 0 | `facefusion` |
| `facefusion/jobs/__init__.py` | CORE | 10 | 0 | 0 | `facefusion/jobs` |
| `facefusion/ffmpeg.py` | LEAF | 9 | 11 | 0 | `facefusion` |
| `facefusion/temp_helper.py` | CORE | 8 | 3 | 0 | `facefusion` |
| `facefusion/face_store.py` | LEAF | 7 | 2 | 0 | `facefusion` |
| `facefusion/audio.py` | LEAF | 6 | 4 | 0 | `facefusion` |
| `facefusion/jobs/job_helper.py` | LEAF | 6 | 1 | 0 | `facefusion/jobs` |
| `facefusion/metadata.py` | LEAF | 6 | 0 | 0 | `facefusion` |
| `facefusion/sanitizer.py` | LEAF | 6 | 1 | 0 | `facefusion` |
| `facefusion/time_helper.py` | LEAF | 6 | 2 | 0 | `facefusion` |
| `facefusion/uis/__init__.py` | LEAF | 6 | 0 | 0 | `facefusion/uis` |
| `facefusion/uis/choices.py` | LEAF | 6 | 2 | 0 | `facefusion/uis` |
| `facefusion/voice_extractor.py` | LEAF | 6 | 7 | 0 | `facefusion` |
| `facefusion/core.py` | ORCHESTRATOR | 4 | 32 | 0 | `facefusion` |
| `facefusion/exit_helper.py` | LEAF | 4 | 5 | 0 | `facefusion` |
| `facefusion/ffmpeg_builder.py` | LEAF | 4 | 2 | 0 | `facefusion` |
| `facefusion/jobs/job_runner.py` | LEAF | 4 | 6 | 0 | `facefusion/jobs` |
| `facefusion/processors/modules/age_modifier/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/background_remover/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/deep_swapper/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/expression_restorer/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_debugger/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_editor/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_enhancer/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_swapper/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_colorizer/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_enhancer/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/lip_syncer/types.py` | LEAF | 4 | 1 | 0 | `facefusion/processors` |
| `facefusion/uis/components/__init__.py` | LEAF | 4 | 0 | 0 | `facefusion/uis` |
| `facefusion/uis/components/about.py` | LEAF | 4 | 3 | 0 | `facefusion/uis` |
| `facefusion/uis/ui_helper.py` | LEAF | 4 | 3 | 0 | `facefusion/uis` |
| `facefusion/args.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion` |
| `facefusion/benchmarker.py` | ORCHESTRATOR | 3 | 11 | 0 | `facefusion` |
| `facefusion/hash_helper.py` | LEAF | 3 | 1 | 0 | `facefusion` |
| `facefusion/jobs/job_list.py` | LEAF | 3 | 4 | 0 | `facefusion/jobs` |
| `facefusion/normalizer.py` | LEAF | 3 | 1 | 0 | `facefusion` |
| `facefusion/processors/modules/age_modifier/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/age_modifier/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/background_remover/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/background_remover/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/deep_swapper/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/deep_swapper/choices.py` | LEAF | 3 | 3 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/expression_restorer/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/expression_restorer/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_debugger/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_debugger/choices.py` | LEAF | 3 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_editor/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_editor/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_enhancer/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_enhancer/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_swapper/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_swapper/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_colorizer/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_colorizer/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_enhancer/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_enhancer/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/lip_syncer/__init__.py` | LEAF | 3 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/lip_syncer/choices.py` | LEAF | 3 | 2 | 0 | `facefusion/processors` |
| `facefusion/uis/components/age_modifier_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/background_remover_options.py` | ORCHESTRATOR | 3 | 10 | 0 | `facefusion/uis` |
| `facefusion/uis/components/deep_swapper_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/download.py` | ORCHESTRATOR | 3 | 14 | 0 | `facefusion/uis` |
| `facefusion/uis/components/execution.py` | ORCHESTRATOR | 3 | 14 | 0 | `facefusion/uis` |
| `facefusion/uis/components/execution_thread_count.py` | LEAF | 3 | 5 | 0 | `facefusion/uis` |
| `facefusion/uis/components/expression_restorer_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_debugger_options.py` | ORCHESTRATOR | 3 | 7 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_editor_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_enhancer_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_swapper_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/frame_colorizer_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/frame_enhancer_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/lip_syncer_options.py` | ORCHESTRATOR | 3 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/processors.py` | LEAF | 3 | 6 | 0 | `facefusion/uis` |
| `facefusion/app_context.py` | LEAF | 2 | 1 | 0 | `facefusion` |
| `facefusion/camera_manager.py` | LEAF | 2 | 1 | 0 | `facefusion` |
| `facefusion/cli_helper.py` | LEAF | 2 | 2 | 0 | `facefusion` |
| `facefusion/curl_builder.py` | LEAF | 2 | 3 | 0 | `facefusion` |
| `facefusion/json.py` | LEAF | 2 | 2 | 0 | `facefusion` |
| `facefusion/memory.py` | LEAF | 2 | 1 | 0 | `facefusion` |
| `facefusion/processors/live_portrait.py` | LEAF | 2 | 1 | 0 | `facefusion/processors` |
| `facefusion/uis/components/memory.py` | ORCHESTRATOR | 2 | 6 | 0 | `facefusion/uis` |
| `facefusion/workflows/core.py` | LEAF | 2 | 4 | 0 | `facefusion/workflows` |
| `facefusion/conda.py` | LEAF | 1 | 1 | 0 | `facefusion` |
| `facefusion/installer.py` | ORCHESTRATOR | 1 | 3 | 0 | `facefusion` |
| `facefusion/locales.py` | LEAF | 1 | 1 | 0 | `facefusion` |
| `facefusion/model_helper.py` | LEAF | 1 | 1 | 0 | `facefusion` |
| `facefusion/processors/modules/age_modifier/core.py` | PLUGIN | 1 | 31 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/age_modifier/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/background_remover/core.py` | PLUGIN | 1 | 24 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/background_remover/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/deep_swapper/core.py` | PLUGIN | 1 | 29 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/deep_swapper/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/expression_restorer/core.py` | PLUGIN | 1 | 30 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/expression_restorer/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_debugger/core.py` | PLUGIN | 1 | 25 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_debugger/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_editor/core.py` | PLUGIN | 1 | 30 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_editor/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_enhancer/core.py` | PLUGIN | 1 | 29 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_enhancer/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_swapper/core.py` | PLUGIN | 1 | 33 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/face_swapper/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_colorizer/core.py` | PLUGIN | 1 | 22 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_colorizer/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_enhancer/core.py` | PLUGIN | 1 | 22 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/frame_enhancer/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/lip_syncer/core.py` | PLUGIN | 1 | 31 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/lip_syncer/locales.py` | PLUGIN | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/processors/pixel_boost.py` | LEAF | 1 | 1 | 0 | `facefusion/processors` |
| `facefusion/program.py` | ORCHESTRATOR | 1 | 14 | 0 | `facefusion` |
| `facefusion/streamer.py` | ORCHESTRATOR | 1 | 12 | 0 | `facefusion` |
| `facefusion/uis/components/benchmark.py` | ORCHESTRATOR | 1 | 4 | 0 | `facefusion/uis` |
| `facefusion/uis/components/benchmark_options.py` | ORCHESTRATOR | 1 | 6 | 0 | `facefusion/uis` |
| `facefusion/uis/components/common_options.py` | ORCHESTRATOR | 1 | 5 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_detector.py` | ORCHESTRATOR | 1 | 10 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_landmarker.py` | ORCHESTRATOR | 1 | 8 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_masker.py` | ORCHESTRATOR | 1 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/face_selector.py` | ORCHESTRATOR | 1 | 14 | 0 | `facefusion/uis` |
| `facefusion/uis/components/instant_runner.py` | ORCHESTRATOR | 1 | 16 | 0 | `facefusion/uis` |
| `facefusion/uis/components/job_list.py` | ORCHESTRATOR | 1 | 10 | 0 | `facefusion/uis` |
| `facefusion/uis/components/job_list_options.py` | ORCHESTRATOR | 1 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/job_manager.py` | ORCHESTRATOR | 1 | 15 | 0 | `facefusion/uis` |
| `facefusion/uis/components/job_runner.py` | ORCHESTRATOR | 1 | 17 | 0 | `facefusion/uis` |
| `facefusion/uis/components/output.py` | ORCHESTRATOR | 1 | 4 | 0 | `facefusion/uis` |
| `facefusion/uis/components/output_options.py` | ORCHESTRATOR | 1 | 10 | 0 | `facefusion/uis` |
| `facefusion/uis/components/preview.py` | ORCHESTRATOR | 1 | 19 | 0 | `facefusion/uis` |
| `facefusion/uis/components/preview_options.py` | ORCHESTRATOR | 1 | 9 | 0 | `facefusion/uis` |
| `facefusion/uis/components/source.py` | ORCHESTRATOR | 1 | 7 | 0 | `facefusion/uis` |
| `facefusion/uis/components/target.py` | ORCHESTRATOR | 1 | 7 | 0 | `facefusion/uis` |
| `facefusion/uis/components/temp_frame.py` | ORCHESTRATOR | 1 | 7 | 0 | `facefusion/uis` |
| `facefusion/uis/components/terminal.py` | ORCHESTRATOR | 1 | 6 | 0 | `facefusion/uis` |
| `facefusion/uis/components/trim_frame.py` | ORCHESTRATOR | 1 | 8 | 0 | `facefusion/uis` |
| `facefusion/uis/components/ui_workflow.py` | ORCHESTRATOR | 1 | 4 | 0 | `facefusion/uis` |
| `facefusion/uis/components/voice_extractor.py` | ORCHESTRATOR | 1 | 8 | 0 | `facefusion/uis` |
| `facefusion/uis/components/webcam.py` | ORCHESTRATOR | 1 | 10 | 0 | `facefusion/uis` |
| `facefusion/uis/components/webcam_options.py` | ORCHESTRATOR | 1 | 7 | 0 | `facefusion/uis` |
| `facefusion/uis/layouts/benchmark.py` | PLUGIN | 1 | 23 | 0 | `facefusion/uis` |
| `facefusion/uis/layouts/default.py` | PLUGIN | 1 | 39 | 0 | `facefusion/uis` |
| `facefusion/uis/layouts/jobs.py` | PLUGIN | 1 | 6 | 0 | `facefusion/uis` |
| `facefusion/uis/layouts/webcam.py` | PLUGIN | 1 | 21 | 0 | `facefusion/uis` |
| `facefusion/uis/overrides.py` | ORCHESTRATOR | 1 | 6 | 0 | `facefusion/uis` |
| `facefusion/workflows/__init__.py` | LEAF | 1 | 0 | 0 | `facefusion/workflows` |
| `facefusion/workflows/image_to_image.py` | ORCHESTRATOR | 1 | 15 | 0 | `facefusion/workflows` |
| `facefusion/workflows/image_to_video.py` | ORCHESTRATOR | 1 | 17 | 0 | `facefusion/workflows` |
| `install.js` | ENTRY | 0 | 0 | 71 | `(root)` |
| `menu.js` | ENTRY | 0 | 0 | 35 | `(root)` |
| `update.js` | ENTRY | 0 | 0 | 33 | `(root)` |
| `run.js` | ENTRY | 0 | 0 | 13 | `(root)` |
| `reset.js` | ENTRY | 0 | 0 | 5 | `(root)` |
| `eslint.config.cjs` | ENTRY | 0 | 0 | 1 | `(root)` |
| `FF.py` | ENTRY | 0 | 4 | 0 | `(root)` |
| `facefusion.py` | ENTRY | 0 | 3 | 0 | `(root)` |
| `facefusion/processors/__init__.py` | PACKAGE | 0 | 0 | 0 | `facefusion/processors` |
| `facefusion/processors/modules/__init__.py` | PACKAGE | 0 | 0 | 0 | `facefusion/processors` |
| `install.py` | ENTRY | 0 | 2 | 0 | `(root)` |
| `tests/__init__.py` | TEST | 0 | 0 | 0 | `tests` |
| `tests/test_audio.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_age_modifier.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_background_remover.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_batch_runner.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_expression_restorer.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_face_debugger.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_face_editor.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_face_enhancer.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_face_swapper.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_frame_colorizer.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_frame_enhancer.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_job_manager.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_job_runner.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_lip_syncer.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_cli_output_scale.py` | TEST | 0 | 5 | 0 | `tests` |
| `tests/test_common_helper.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_config.py` | TEST | 0 | 2 | 0 | `tests` |
| `tests/test_curl_builder.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_download.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_execution.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_face_analyser.py` | TEST | 0 | 11 | 0 | `tests` |
| `tests/test_ffmpeg.py` | TEST | 0 | 9 | 0 | `tests` |
| `tests/test_ffmpeg_builder.py` | TEST | 0 | 2 | 0 | `tests` |
| `tests/test_filesystem.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_inference_manager.py` | TEST | 0 | 4 | 0 | `tests` |
| `tests/test_job_helper.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_job_list.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_job_manager.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_job_runner.py` | TEST | 0 | 6 | 0 | `tests` |
| `tests/test_json.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_memory.py` | TEST | 0 | 2 | 0 | `tests` |
| `tests/test_normalizer.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_process_manager.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_program_helper.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_sanitizer.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_state_manager.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_temp_helper.py` | TEST | 0 | 5 | 0 | `tests` |
| `tests/test_time_helper.py` | TEST | 0 | 1 | 0 | `tests` |
| `tests/test_translator.py` | TEST | 0 | 3 | 0 | `tests` |
| `tests/test_vision.py` | TEST | 0 | 4 | 0 | `tests` |

## Files that load modules by name

The graph is incomplete around these. They decide at runtime what to import.

- `facefusion/inference_manager.py`
- `facefusion/processors/core.py`
- `facefusion/translator.py`
- `facefusion/uis/core.py`

## Coupled by history (changed together in the same commit)

These links exist even when no import connects the files.

| File A | File B | Commits together |
|---|---|---:|
| `install.js` | `package.json` | 29 |
| `install.js` | `pinokio.js` | 29 |
| `install.js` | `update.js` | 29 |
| `package.json` | `pinokio.js` | 27 |
| `package.json` | `update.js` | 27 |
| `pinokio.js` | `update.js` | 26 |
| `menu.js` | `run.js` | 6 |
| `install.js` | `menu.js` | 5 |
| `install.js` | `start.js` | 5 |
| `menu.js` | `start.js` | 5 |
| `menu.js` | `pinokio.js` | 4 |
| `pinokio.js` | `start.js` | 4 |
| `LICENSE.md` | `package.json` | 3 |
| `README.md` | `install.js` | 3 |
| `README.md` | `package.json` | 3 |

