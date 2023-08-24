from qgis.core import QgsProject, Qgis, QgsProcessingContext, QgsProcessingFeedback, QgsProcessingMultiStepFeedback, QgsRasterLayer, QgsProcessing, QgsVectorLayer
from qgis import processing

def process_ndwi_function(dlg):
    current_tab_index = dlg.NDWI.tabText(dlg.NDWI.currentIndex())
    print(current_tab_index)
    
    if current_tab_index == 'Land-Water Mask(NDWI)':
        dlg.progressBar.setValue(0)
        greenBandName = int(dlg.greenBandComboBoxNDWI.currentText())
        nirBandName = int(dlg.nirBandComboBoxNDWI.currentText())

        output_ndwi = dlg.outputLineEditNDWI.text()

        outputs = {}
        
        alg_params = {
            'BAND_A': greenBandName,
            'BAND_B': nirBandName,
            'FORMULA': '(A-B)/(A+B)',
            'INPUT_A': getBandCount(dlg),
            'INPUT_B': getBandCount(dlg),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        # Prepare the processing context and feedback
        context = QgsProcessingContext()
        model_feedback = QgsProcessingFeedback()
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)

        def update_progress(value):
            dlg.progressBar.setValue(int(value))

        feedback.setProgressText('Processing...')
        feedback.progressChanged.connect(update_progress)

        # Compute NDWI
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        # feedback.setProgress(50)

        if feedback.isCanceled():
            return

        feedback.setCurrentStep(1)

        # Reclassify by table
        alg_params = {
            'DATA_TYPE': 1,  # Float32
            'INPUT_RASTER': outputs['RasterCalculator']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,  # min < value <= max
            'RASTER_BAND': 1,
            'TABLE': ['-1','0.1','1','0.1','1','2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        
        outputs['ReclassifybyTable'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        feedback.setProgress(100)

        vect_params = {'INPUT': outputs['ReclassifybyTable']['OUTPUT'],'BAND':1,'FIELD':'DN', 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        outputs['polygonize'] = processing.run('gdal:polygonize', vect_params, context=context, feedback=model_feedback)

        if outputs['polygonize']['OUTPUT']:
            # NDWI calculation successful
            print("NDWI calculation successful. Output saved at:", outputs['polygonize']['OUTPUT'])
            return outputs['polygonize']['OUTPUT']
        else:
            # NDWI calculation failed
            print("NDWI calculation failed.")
            return None  # or return some kind of error signal

def getBandCount(dlg):
    rasterlayerName = dlg.multibandRasterComboboxNDWI.currentText()
    layers = QgsProject.instance().mapLayersByName(rasterlayerName)
    if layers:
        selectedRasterLayer = layers[0]
        print(selectedRasterLayer)
        num_bands = selectedRasterLayer.bandCount()
        
        dlg.greenBandComboBoxNDWI.clear()
        dlg.greenBandComboBoxNDWI.addItems([str(num) for num in range(1, num_bands + 1)])
        
        dlg.nirBandComboBoxNDWI.clear()
        dlg.nirBandComboBoxNDWI.addItems([str(num) for num in range(1, num_bands + 1)])
        
        return selectedRasterLayer
    else:
        print("No layers in the project")
