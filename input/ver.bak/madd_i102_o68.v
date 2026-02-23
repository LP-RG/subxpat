module madd_i102_o68 (a, b, c, r);
input [33:0] a,b,c;
output [67:0] r;

assign r = (a * b) + c;

endmodule
