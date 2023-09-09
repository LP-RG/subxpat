module top (a,b,r);
input [4:0] a,b;
output [5:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
