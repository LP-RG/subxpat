module madd_i72_o48 (a, b, c, r);
input [23:0] a,b,c;
output [47:0] r;

assign r = (a * b) + c;

endmodule
