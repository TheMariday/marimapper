export var pixel_to_light = -1
export var turn_on=true

export function render(index) {
  if(index == pixel_to_light && turn_on){
    rgb(1,1,1)
  } else{
    rgb(0,0,0)
  }
}