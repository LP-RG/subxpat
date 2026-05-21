module adder_i384_o193(a,b,r);
input [191:0] a,b;
output [192:0] r;

assign r = a+b;

endmodule
