const path = require('path');

module.exports = () =>
{
	const config =
	{
		daemon: true,
		cmd:
		{
			'Default': 'C:/Python314/python.exe facefusion.py run',
			'Default+Jobs': 'C:/Python314/python.exe facefusion.py run --ui-layouts default jobs',
			'Benchmark': 'C:/Python314/python.exe facefusion.py run --ui-layouts benchmark',
			'Webcam': 'C:/Python314/python.exe facefusion.py run --ui-layouts webcam'
		},
		run:
		[
			{
				method: 'local.set',
				params:
				{
					mode: '{{ input.mode }}'
				}
			},
			{
				method: 'shell.run',
				params:
				{
					message: 'git checkout --quiet -- facefusion',
					path: 'facefusion'
				}
			},
			{
				method: 'shell.run',
				params:
				{
					message: '{{ self.cmd[local.mode] }}',
					path: 'facefusion',
					conda:
					{
						path: path.resolve(__dirname, '.env')
					},
					on:
					[
						{
							event: '/(http:\/\/[0-9.:]+)/',
							done: true
						}
					]
				}
			},
			{
				method: 'local.set',
				params:
				{
					url: '{{ input.event[0] }}'
				}
			}
		]
	};

	return config;
};
