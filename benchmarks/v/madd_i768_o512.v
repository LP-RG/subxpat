module madd_i768_o512 (a, b, c, r);
input [255:0] a,b,c;
output [511:0] r;

assign r = (a * b) + c;

endmodule
