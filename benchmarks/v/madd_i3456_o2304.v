module madd_i3456_o2304 (a, b, c, r);
input [1151:0] a,b,c;
output [2303:0] r;

assign r = (a * b) + c;

endmodule
