module adder_i65536_o32769(a,b,r);
input [32767:0] a,b;
output [32768:0] r;

assign r = a+b;

endmodule
