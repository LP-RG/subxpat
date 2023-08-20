module top (a,b,r);
input [2:0] a;
input [2:0] b;
output [5:0] r;

assign r = a * b;

endmodule

