module adder_i128_o65(a,b,r);
input [63:0] a,b;
output [65:0] r;

assign r = a+b;

endmodule
