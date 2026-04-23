module madd_i2688_o1792 (a, b, c, r);
input [895:0] a,b,c;
output [1791:0] r;

assign r = (a * b) + c;

endmodule
